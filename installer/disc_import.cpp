// Internal native importer: exact supported disc in, private derived files out.
// No Python, BIOS, mod executable, source writes or source-path logging.
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <nlohmann/json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <cmath>
#include <stdexcept>
namespace fs=std::filesystem;
using json=nlohmann::json;
struct ImportError:std::runtime_error{using std::runtime_error::runtime_error;};
void require(bool ok,const char* error){if(!ok)throw ImportError(error);}
struct Hash {
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    Hash(){require(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"Hash initialization failed.");require(BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0)>=0,"Hash initialization failed.");}
    ~Hash(){if(hash)BCryptDestroyHash(hash);if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);}
    void add(const char* data,size_t count){require(count<=0xffffffff && BCryptHashData(hash,(PUCHAR)data,ULONG(count),0)>=0,"Disc verification failed.");}
    std::string finish(){unsigned char result[32];require(BCryptFinishHash(hash,result,32,0)>=0,"Disc verification failed.");std::string text;for(auto c:result){text+="0123456789abcdef"[c>>4];text+="0123456789abcdef"[c&15];}return text;}
};
std::string digest(const fs::path& path){std::ifstream file(path,std::ios::binary);require(bool(file),"Couldn't read the disc.");Hash hash;std::vector<char> buffer(4*1024*1024);while(file){file.read(buffer.data(),buffer.size());hash.add(buffer.data(),size_t(file.gcount()));}require(file.eof(),"Couldn't read the disc.");return hash.finish();}
std::string digest(const std::vector<char>& data){Hash hash;hash.add(data.data(),data.size());return hash.finish();}
json load(const fs::path& path){std::ifstream stream(path);require(bool(stream),"Import data is missing.");json value;stream>>value;return value;}
uint32_t u32(const std::vector<char>& data,size_t offset){require(offset+4<=data.size(),"The disc is truncated.");uint32_t v;std::memcpy(&v,data.data()+offset,4);return v;}
struct Disc {
    std::ifstream file;uint64_t size;
    Disc(const fs::path& path):file(path,std::ios::binary),size(fs::file_size(path)){require(bool(file),"Couldn't read the disc.");}
    std::vector<char> read(uint64_t offset,size_t count){require(offset<=size && count<=size-offset,"The disc is truncated.");std::vector<char> data(count);file.clear();file.seekg(offset);file.read(data.data(),count);require(size_t(file.gcount())==count,"The disc is truncated.");return data;}
    std::pair<uint64_t,uint32_t> member(std::string path){auto pvd=read(16*2048,2048);require(std::memcmp(pvd.data()+1,"CD001",5)==0,"Pick a supported ISO disc image.");std::vector<char> record(pvd.begin()+156,pvd.begin()+190);
        size_t start=0;while(start<path.size()){auto end=path.find('/',start);auto part=path.substr(start,end==std::string::npos?end:end-start);auto directory=read(uint64_t(u32(record,2))*2048,u32(record,10));bool found=false;
            for(size_t at=0;at<directory.size();){unsigned length=(unsigned char)directory[at];if(!length){at=(at/2048+1)*2048;continue;}require(length>=34 && at+length<=directory.size(),"The disc directory is damaged.");auto nameLength=(unsigned char)directory[at+32];require(33u+nameLength<=length,"The disc directory is damaged.");std::string name(directory.data()+at+33,nameLength);name=name.substr(0,name.find(';'));if(name==part){record.assign(directory.begin()+at,directory.begin()+at+length);found=true;break;}at+=length;}
            require(found,"A required game file is missing.");if(end==std::string::npos)break;require(record[25]&2,"The disc directory is damaged.");start=end+1;}
        return {uint64_t(u32(record,2))*2048,u32(record,10)};
    }
};
void progress(const char* stage,unsigned percent){std::cout<<json{{"stage",stage},{"percent",percent}}.dump()<<std::endl;}
int wmain(int argc,wchar_t** argv){try{
    require(argc==4,"Select a disc and an empty app-data destination.");fs::path source=fs::absolute(argv[1]),destination=fs::absolute(argv[2]),configuration=fs::absolute(argv[3]);
    require(!fs::exists(destination) || fs::is_empty(destination),"The import destination must be empty.");
    progress("verify",0);auto hash=digest(source);auto table=load(configuration/"supported-discs.json");json disc;
    for(auto& candidate:table.at("discs"))if(candidate.at("sha256")==hash && candidate.at("size")==fs::file_size(source))disc=candidate;
    if(disc.is_null()){std::cout<<json{{"error","That disc isn't supported yet: Power Scale BETA 1.5.1 is required."},{"sha256",hash},{"size",fs::file_size(source)}}.dump()<<std::endl;return 2;}
    auto recipe=load(configuration/"map-recipe.json");require(recipe.at("schema")==1 && recipe.at("scale")==2,"The map import recipe isn't supported.");
    require(fs::file_size(configuration/"map-fields.bin")<=128*1024*1024,"Invalid map recipe size.");std::ifstream fieldFile(configuration/"map-fields.bin",std::ios::binary);std::vector<unsigned char> fields((std::istreambuf_iterator<char>(fieldFile)),{});require(!fieldFile.bad() && fields.size()==fs::file_size(configuration/"map-fields.bin"),"Couldn't read the map recipe.");
    // Source copy plus extracted module archives and a margin for derived art.
    auto parent=destination.parent_path();fs::create_directories(parent);require(fs::space(parent).available>=fs::file_size(source)*2+1024*1024*1024ull,"Not enough space: import needs 10 GB.");
    fs::create_directories(destination);auto temporary=destination/"disc.partial";
    progress("copy",10);fs::copy_file(source,temporary,fs::copy_options::none);
    require(digest(temporary)==hash,"The disc changed while it was being copied.");
    const bool reverse=disc.at("expanded").get<bool>();
    fs::copy_file(temporary,destination/(reverse?"expanded-2x.iso":"original.iso"),fs::copy_options::none);
    {
        require(hash==recipe.at(reverse?"output_sha256":"source_sha256"),"The map recipe belongs to a different disc.");std::fstream target(temporary,std::ios::binary|std::ios::in|std::ios::out);require(bool(target),"Couldn't prepare the map copy.");unsigned index=0;
        for(auto& patch:recipe.at("patches")){uint64_t offset=patch.at("offset");size_t length=patch.at("length");require(offset<=fs::file_size(source) && length<=fs::file_size(source)-offset && length<=64*1024*1024,"Invalid map import bounds.");std::vector<char> raw(length);target.seekg(offset);target.read(raw.data(),length);require(size_t(target.gcount())==length && digest(raw)==patch.at(reverse?"after_sha256":"before_sha256"),"The map copy failed verification.");
            size_t cursor=patch.at("field_offset"),end=cursor+patch.at("field_bytes").get<size_t>();require(end>=cursor && end<=fields.size(),"Invalid map recipe bounds.");size_t at=0;
            for(size_t i=0;i<patch.at("field_count").get<size_t>();++i){uint32_t delta=0;unsigned shift=0;unsigned char byte;
                do{require(cursor<end && shift<=28,"Invalid map coordinate recipe.");byte=fields[cursor++];delta|=uint32_t(byte&127)<<shift;shift+=7;}while(byte&128);
                require((i==0 || delta>0) && delta<=length && at<=length-delta,"Invalid map coordinate recipe.");at+=delta;require(at%4==0 && at+4<=length,"Invalid map coordinate recipe.");float value;std::memcpy(&value,raw.data()+at,4);value*=reverse?.5f:2.f;require(std::isfinite(value),"The map coordinate is invalid.");std::memcpy(raw.data()+at,&value,4);}
            require(cursor==end,"Invalid map recipe length.");
            require(digest(raw)==patch.at(reverse?"before_sha256":"after_sha256"),"The expanded map failed verification.");target.seekp(offset);target.write(raw.data(),length);require(bool(target),"Couldn't save the expanded map.");progress("maps",20+unsigned(40*++index/recipe.at("patches").size()));}
        target.flush();require(bool(target),"Couldn't save the expanded map.");
    }
    require(digest(temporary)==recipe.at(reverse?"source_sha256":"output_sha256"),"The prepared disc failed verification.");
    fs::rename(temporary,destination/(reverse?"original.iso":"expanded-2x.iso"));Disc image(destination/"expanded-2x.iso");json files=json::object();
    for(const auto& name:{"SLUS_216.78","BIN/MOD.BIN","BIN/DBZP.BIN","DATA/MOD.AFS","DATA/DLC.AFS"}){auto [offset,length]=image.member(name);auto output=destination/"input"/name;fs::create_directories(output.parent_path());std::ofstream target(output,std::ios::binary);Hash memberHash;
        for(uint64_t done=0;done<length;){size_t count=size_t(std::min(uint64_t(4*1024*1024),uint64_t(length)-done));auto buffer=image.read(offset+done,count);target.write(buffer.data(),count);memberHash.add(buffer.data(),count);done+=count;}require(bool(target),"Couldn't extract the game files.");files[name]=json{{"size",length},{"sha256",memberHash.finish()}};
    }
    json receipt{{"schema",1},{"tool_version","native-import-0.1"},{"disc_sha256",hash},{"original_disc_sha256",recipe.at("source_sha256")},{"prepared_disc_sha256",recipe.at("output_sha256")},{"adapter_id",disc.at("adapter_id")},{"files",files}};
    std::ofstream saved(destination/"import-receipt.json");saved<<receipt.dump(2);require(bool(saved),"Couldn't save the import receipt.");progress("done",100);return 0;
}catch(const ImportError& error){std::cout<<json{{"error",error.what()}}.dump()<<std::endl;return 1;}catch(const std::exception&){std::cout<<json{{"error","Disc import failed; check the selected disc and available space."}}.dump()<<std::endl;return 1;}}
