"""Editable feature controls shared by settings UI and runtime installers.

Only options with a runtime consumer belong here. Engine corruption guards are
not gameplay features and are deliberately kept separate from preferences.
Keys, validation ranges and choice values are part of saved files: never rename
or tighten them. Editors use STEPS/UI_LIMITS below instead.
"""
import math
import input_binding

# key: (default, kind, minimum/choices, maximum, UI group, label)
# The group names match mod_settings.GROUPS, which also sets the display order.
OPTIONS = {
    'native_mode_cover': (False,'bool',None,None,'Menus','Decorative mode loading cover'),
    'cpu_transform_allies': ('native','choice',('native','more_often','outmatched'),None,'CPU tactics','Allied CPU transformations'),
    'cpu_transform_enemies': ('native','choice',('native','more_often','outmatched'),None,'CPU tactics','Enemy CPU transformations'),
    'cpu_tactics_preset': ('native','choice',('native','aggressive','relentless'),None,'CPU tactics','CPU tactics difficulty'),
    'hud_style': ('game_overhead','choice',('game_overhead','overhead_only'),None,'HUD','HUD style'),
    'hud_overhead_shape': ('hexagon','choice',('off','hexagon','ring','plate'),None,'HUD','Overhead shape'),
    'hud_overhead_names': ('off','choice',('off','tiny','normal','focused','all'),None,'HUD','Overhead names'),
    'hud_overhead_ki_pips': (True,'bool',None,None,'HUD','Overhead ki stocks'),
    'hud_overhead_detail': ('focused','choice',('owner','focused','allies','everyone'),None,'HUD','Detailed overhead HUD'),
    'hud_overhead_portraits': (True,'bool',None,None,'HUD','Overhead portraits'),
    'hud_contestant_list': (False,'bool',None,None,'HUD','Contestant list'),
    'hud_panel_scale_percent': (65,'int',50,130,'HUD','Overhead HUD size (%)'),
    'hud_panel_opacity_percent': (50,'int',20,100,'HUD','Overhead HUD opacity (%)'),
    'lockoff_enabled': (True,'bool',None,None,'Controls','Enable manual lock-off'),
    'lockoff_button': ('l3','button',input_binding.BUTTONS,None,'Controls','Lock-off button'),
    'lockoff_hold_seconds': (0.5,'float',0,3600,'Controls','Lock-off hold time (seconds; 0 = tap)'),
    'lockoff_target_hud': ('single_enemy','choice',('single_enemy','hide','show'),None,'HUD','Target HUD while unlocked'),
    'language': ('en','choice',('en','es'),None,'Menus','Language / Idioma'),
    'rush_cinematics': (False,'bool',None,None,'Cinematics','Rush attacks: shared camera and pause'),
    'true_body_change': (False,'bool',None,None,'Fighters','Ginyu: exchange bodies with the actual opponent'),
    'ginyu_stolen_abilities': (False,'bool',None,None,'Fighters','Ginyu can use stolen-body abilities'),
    'npc_transform_chance_percent': (100,'int',0,100,'Fighters','CPU transformation chance (%; 100 = normal)'),
    'native_mode_menu_enabled': (True,'bool',None,None,'Menus','Mod mode menus'),
    'menu_toggle_button': ('select','button',('select','l3','r3','start','l2','r2','l1','r1','square'),None,'Menus','Menu switch button'),
    'show_menu_toggle_hint': (True,'bool',None,None,'Menus','Show the menu switch button hint'),
    'coop_independent_selection': (True,'bool',None,None,'Character select','Each player picks their own assigned fighters'),
    'all_controllers_character_select': (False,'bool',None,None,'Character select','Allow all controllers during character selection'),
    'show_player_slot_labels': (True,'bool',None,None,'Character select','Show player numbers above selection slots'),
    'training_cpu_behavior': ('idle','choice',('idle','fight'),None,'Training','CPU behavior'),
    'training_refill_health': (True,'bool',None,None,'Training','Refill health and prevent knockouts'),
    'training_health_delay_seconds': (2.0,'float',0,30,'Training','Health refill delay after damage (seconds)'),
    'training_refill_ki': (True,'bool',None,None,'Training','Refill ki'),
    'training_refill_stocks': (True,'bool',None,None,'Training','Refill blast stocks'),
    'spectator_takeover_enabled': (True,'bool',None,None,'Spectating','Allow taking over living CPU teammates'),
    'spectate_fallen_fighters': (True,'bool',None,None,'Spectating','Allow spectating fallen fighters'),
    'show_takeover_hints': (True,'bool',None,None,'Spectating','Show takeover button hint'),
    'show_takeover_confirmation': (True,'bool',None,None,'Spectating','Show takeover confirmation'),
    'takeover_hint_seconds': (1.0,'float',0,15,'Spectating','Takeover hint delay (seconds)'),
    'takeover_confirmation_seconds': (3.0,'float',0.25,15,'Spectating','Takeover confirmation time (seconds)'),
    'extra_character_voices': (True,'bool',None,None,'Fighters','Extra fighter voice lines'),
    'extra_character_intros': (False,'bool',None,None,'Cinematics','Introductions for extra fighters'),
    'loading_animation_speed_percent': (100,'int',25,400,'Menus','Loading animation speed (%; 100 = normal)'),
    'expanded_maps': (False,'bool',None,None,'Launch options (restart)','Experimental 2x maps (restart)'),
    'widescreen_patch': (False,'bool',None,None,'Launch options (restart)','PCSX2 16:9 widescreen patch (restart; automatic for BT4)'),
    # Applied by the launcher for its session only (presentation_settings), restored when PCSX2 closes.
    'fast_disc_loading': (True,'bool',None,None,'Launch options (restart)','Fast disc loading (restart)'),
    'emulated_cpu_speed': ('default','choice',('default','130','180','300'),None,'Launch options (restart)','Emulated PS2 CPU speed (restart)'),
    'canonical_giants': (False,'bool',None,None,'Giants','Larger canonical-style giants (expanded maps recommended)'),
    'giant_size_multiplier': (2.0,'float',1,4,'Giants','Giant size multiplier'),
    'giant_attack_speed_percent': (75,'int',25,100,'Giants','Giant ordinary attack speed (%)'),
    'giant_damage_percent': (150,'int',100,500,'Giants','Giant attack damage (%)'),
    'giant_armor_levels': (1,'int',0,5,'Giants','Extra giant stagger resistance (0 = native)'),
    'giant_camera_distance_percent': (150,'int',100,250,'Giants','Giant follow camera distance (%)'),
    'keep_preparation_diagnostics': (False,'bool',None,None,'Diagnostics','Keep preparation RAM dumps (uses a lot of disk space)'),
    'capture_freeze_dumps': (False,'bool',None,None,'Diagnostics','Save a large diagnostic snapshot if a match freezes'),
    'record_battle_diagnostics': (False,'bool',None,None,'Diagnostics','Write diagnostic battle history to disk'),
    'coop_fusion_swap_seconds': (20,'int',5,60,'Fusion','Fusion control swap interval (seconds)'),
    'show_fuse_prompt': (True,'bool',None,None,'Fusion','Show R3 fusion prompt'),
    'fusion_duration_enabled': (False,'bool',None,None,'Fusion','Timed fusion and automatic defusion'),
    'fusion_duration_seconds': (40,'int',1,300,'Fusion','Fusion time limit (seconds)'),
    'fusion_time_by_form': (False,'bool',None,None,'Fusion','Fusion time drains faster in stronger forms'),
    'fusion_form_penalty': ('normal','choice',('mild','normal','heavy'),None,'Fusion','Fusion form drain strength'),
    'show_fusion_timer': (True,'bool',None,None,'Fusion','Show remaining fusion time'),
    'fusion_defusion_animation': (True,'bool',None,None,'Fusion','Play power-down animation before defusion'),
    'show_fusion_control_owner': (True,'bool',None,None,'Fusion','Show fusion control owner and roles'),
    'show_fusion_control_countdown': (True,'bool',None,None,'Fusion','Show time until control or role swap'),
    'split_hud_style': ('native','choice',('native','compact'),None,'Split-screen HUD','Split-screen HUD style'),
    'split_hud_scale_percent': (100,'int',80,140,'Split-screen HUD','Top-row HUD size (%)'),
    'split_hud_layout': ('top','choice',('top','top_bottom'),None,'Split-screen HUD','Split-screen HUD layout'),
    'split_hud_filter': ('linear','choice',('nearest','linear'),None,'Split-screen HUD','HUD texture filtering'),
    'coop_hud_layout': ('players','choice',('players','targets'),None,'Split-screen HUD','Co-op HUD panels'),
    'show_hud_portraits': (True,'bool',None,None,'Split-screen HUD','Fighter portraits (native style)'),
    'show_hud_sparking_effects': (True,'bool',None,None,'Split-screen HUD','Sparking lightning (native style)'),
    'hud_damage_trail_seconds': (0.5,'float',0,3,'Split-screen HUD','Health damage trail (seconds; 0 = off)'),
    'revive_radius': (40.0,'float',5,200,'Revival','Revival distance (world units)'),
    'revive_health_bars': (2.0,'float',0.25,10,'Revival','Health bars restored'),
    'revive_recovery_seconds': (1.0,'float',0.25,10,'Revival','Minimum protected get-up time (seconds)'),
    'show_revive_ring': (True,'bool',None,None,'Revival','Show revival range ring'),
    'revive_ring_opacity': (0.45,'float',0,1,'Revival','Revival ring opacity'),
    'revive_ring_wave_height': (8.0,'float',0,80,'Revival','Revival ring wave height (0 = flat)'),
    'revive_ring_wave_speed': (1.0,'float',0,5,'Revival','Revival ring wave speed (cycles per second)'),
}
DEFAULTS={key:row[0] for key,row in OPTIONS.items()}

# Editor metadata, deliberately separate from the six-field rows above (their
# unpacking is shared by several modules). Every whole-number or decimal setting
# of mod_settings.ui_fields() has a step; whole-number steps stay int.
STEPS = {'coop_fusion_swap_seconds': 5,
    'hud_panel_scale_percent': 5, 'hud_panel_opacity_percent': 5,
    'lockoff_hold_seconds': 0.25,
    'lockon_hold_seconds': 0.25, 'revive_stock_cost': 1, 'revive_channel_seconds': 0.25,
    'npc_transform_chance_percent': 5, 'training_health_delay_seconds': 0.25,
    'takeover_hint_seconds': 0.25, 'takeover_confirmation_seconds': 0.25,
    'loading_animation_speed_percent': 5, 'giant_size_multiplier': 0.25,
    'giant_attack_speed_percent': 5, 'giant_damage_percent': 5, 'giant_armor_levels': 1,
    'giant_camera_distance_percent': 5, 'fusion_duration_seconds': 5, 'split_hud_scale_percent': 1,
    'hud_damage_trail_seconds': 0.25, 'revive_radius': 5, 'revive_health_bars': 0.25,
    'revive_recovery_seconds': 0.25, 'revive_ring_opacity': 0.05, 'revive_ring_wave_height': 1,
    'revive_ring_wave_speed': 0.25,
}
# Optional tighter (minimum, maximum) for the editors only. Saved values outside
# it stay valid; a press moves them back inside.
UI_LIMITS = {'lockon_hold_seconds': (0, 10), 'lockoff_hold_seconds': (0,10),
             'hud_panel_scale_percent': (50,120), 'hud_panel_opacity_percent': (30,100)}
UI_PRESETS = {'coop_fusion_swap_seconds': (5,10,15,20,30,45,60),'hud_panel_scale_percent': (50,65,80,100,120),
              'hud_panel_opacity_percent': (30,50,70,100)}
UI_CHOICES = {'hud_overhead_names': ('off','tiny','normal')}
# Read by the launcher before PCSX2 starts; a saved change waits for Play to restart.
RESTART_KEYS = ('widescreen_patch', 'fast_disc_loading', 'emulated_cpu_speed', 'expanded_maps', 'native_mode_cover')
BIG_STEPS = 10


def validate_into(result):
    for key,(default,kind,low,high,group,label) in OPTIONS.items():
        value=result.setdefault(key,default)
        if kind=='bool':valid=type(value)is bool
        elif kind in ('choice','button'):valid=type(value)is str and value in low
        elif kind=='int':valid=type(value)is int and low<=value<=high
        else:valid=type(value)in(int,float)and math.isfinite(value)and low<=value<=high
        if not valid:raise ValueError(f'Invalid {label.lower()}: {value!r}')
    return result


def ui_range(key):
    """(minimum, maximum) offered by the editors for a numeric setting."""
    import mod_settings  # Deferred: mod_settings imports this module.
    _,kind,low,high,_,_=mod_settings.ui_fields()[key]
    if kind not in ('int','float'):raise ValueError(f'{key} is not numeric')
    return UI_LIMITS.get(key,(low,high))


def grid(key, anchors=None):
    """Sorted editor stops: multiples of the step from zero inside the editor
    range, both ends of that range, the code default and the installed default."""
    import mod_settings
    _,kind,_,_,_,_=mod_settings.ui_fields()[key]
    if key in UI_PRESETS:return list(UI_PRESETS[key])
    low,high=ui_range(key);step=STEPS[key]
    if anchors is None:
        installed=mod_settings.installed_defaults() or {}
        anchors=[mod_settings.DEFAULTS[key]]+([installed[key]] if key in installed else [])
    if kind=='int':
        points={k*step for k in range(-(-low//step),high//step+1)}|{low,high}
        points|={a for a in anchors if type(a) is int and low<=a<=high}
    else:
        first,last=math.ceil(low/step-1e-9),math.floor(high/step+1e-9)
        points={float(round(k*step,6)) for k in range(first,last+1)}|{float(low),float(high)}
        points|={float(a) for a in anchors if type(a) in (int,float) and math.isfinite(a) and low<=a<=high}
    result=[]
    for point in sorted(points):
        if not result or point-result[-1]>1e-9:result.append(point)
    return result


def step_value(key, value, direction, big=False, *, anchors=None):
    """The value one editor press away, shared by the desktop and in-game editors.

    Numbers move to the next grid stop in `direction` (+1/-1); an off-grid value
    goes to the nearest stop that way. `big` moves ten stops, stopping at the
    range end. A value with nothing further that way is returned unchanged.
    Choices and buttons cycle; `big` jumps to the first/last. Booleans toggle;
    `big` sets False (-1) or True (+1). Whole numbers stay int.
    """
    import mod_settings
    _,kind,low,_,_,_=mod_settings.ui_fields()[key]
    if direction not in (-1,1):raise ValueError('direction must be -1 or 1')
    if kind=='bool':return direction>0 if big else not value
    if kind in ('choice','button'):
        low=UI_CHOICES.get(key,low)
        if big:return low[-1] if direction>0 else low[0]
        return low[(low.index(value)+direction)%len(low)] if value in low else low[0]
    stops=grid(key,anchors)
    ahead=[p for p in stops if p>value+1e-9] if direction>0 else [p for p in reversed(stops) if p<value-1e-9]
    if not ahead:return value
    return ahead[min(BIG_STEPS if big else 1,len(ahead))-1]
