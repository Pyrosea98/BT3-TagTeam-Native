using System;
using System.IO;
using System.Diagnostics;
using System.Windows.Forms;
class Play {
 [STAThread] static void Main(){
  string root=AppDomain.CurrentDomain.BaseDirectory;
  try{
   var p=new ProcessStartInfo(Path.Combine(root,"runtime","pythonw.exe"),"\""+Path.Combine(root,"app.pyw")+"\"");
   p.WorkingDirectory=root;p.UseShellExecute=false;p.CreateNoWindow=true;
   p.EnvironmentVariables["PYTHONDONTWRITEBYTECODE"]="1";
   Process.Start(p);
  }catch(Exception e){MessageBox.Show(e.Message,"BT3 Tag Team",MessageBoxButtons.OK,MessageBoxIcon.Error);}
 }
}
