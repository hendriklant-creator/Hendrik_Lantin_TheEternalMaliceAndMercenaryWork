from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController #  for everything to do with first-person movement
from ursina.prefabs.ursfx import ursfx
import random, math, json, textwrap, sys
import builtins as _builtins

DEV_MODE = False

# starts, but tests all textures and files to see what is missing from the project
#This came super helpful in seeing if any textures aren't loading, also early on to understand where to put assets i used
#the interact function to test which texture was aligned to which asset, to easily change them by knowing their name
#This worked exceptionally well, because the whole game engine is built on assets found by name, not by path, with a couple exceptions
#big assets or features with a lot of specific files were not just by name findable - everything with the village asset, DOOM MAP and textures, ENEMY SPRITES

#I USED AI TO CREATE THE DEV MODE! SO THIS ALSO AFFECTED SOME OF THE OTHER CODE BECAUSE THE FAILSAFE TO PRINT SOMETHING WHEN A TEXTURE WAS MISSING ALSO PRINTED THERE
# i found no tutorials on this and had no clue where to even start!
#This worked marvelously - i can also still test whether a file is used or not, by running "python launcher.py loud".


QUIET_START = 'loud' not in [str(a).lower() for a in sys.argv[1:]]
_real_print = _builtins.print


def print(*args, **kwargs):  # args is accepting of any numebr or ordinary arguments and putting them in a list
    if not QUIET_START: # together the point is that it just takes EVERY FILE IN THE PROJECT
        return _real_print(*args, **kwargs)
    if args and isinstance(args[0], str) and args[0].lstrip().startswith('!!'): # this is the code to print the missing texture when it finds any during python launcher.py loud and gets rid of anything else.
        return _real_print(*args, **kwargs) # if not opening the python launcher.py loud then just do normal prints
    return None

# app, window, resolution, fullscreen
# note to self window settings must always come AFTER Ursina() always

app = Ursina()

# WHICH FOLDER ARE MY ASSETS ACTUALLY IN?
# ursina decides this ONCE, from sys.argv[0], the moment it is imported:
#
#     asset_folder = Path(sys.argv[0]).parent          # ursina/application.py
#
# So the answer depends entirely on what was started. launcher.py at the project
# root gives the root, which is right and is what the launcher is for. Start
# this file on its own instead - Run on game.py in PyCharm, or any wrapper that
# imports ursina after sys.argv[0] has been rewritten - and it comes out as
# src/, which contains one .py file and nothing else. The game then starts
# perfectly, the menu comes up, and not one texture, model or sound loads,
# because the scan is looking in a folder with no assets in it.
#
# So i do not trust the guess. media/ is the tell: whichever folder up the
# chain actually has the assets in it is the one that gets used.
_ASSET_MARKERS = ('media', 'assets and textures')


def _looks_like_the_asset_root(folder):
    try:
        return any((folder / name).is_dir() for name in _ASSET_MARKERS)
    except Exception:
        return False


try:
    from pathlib import Path as _Path
    _HERE = _Path(__file__).resolve().parent
    _picked = _Path(str(application.asset_folder)).resolve()

    _fixed = None
    if not _looks_like_the_asset_root(_picked):
        # up the chain: next to this file, one above it, one above the guess.
        for _cand in (_HERE, _HERE.parent, _HERE.parent.parent, _picked.parent):
            if _looks_like_the_asset_root(_cand):
                _fixed = _cand
                break

    if _fixed is not None and _fixed != _picked:
        print('assets: ursina guessed %s, and there is no %s folder in it.\n'
              '        using %s instead - that is where the assets are.'
              % (_picked, ' or '.join(_ASSET_MARKERS), _fixed))
        application.asset_folder = _fixed
        # AND TELL PANDA3D SEPARATELY. It keeps its own copy of the search
        # path, built when ursina was imported, and fonts and anything loaded
        # by plain name come through that rather than through my own scan - so
        # setting asset_folder on its own fixes half of it and leaves the other
        # half silently empty.
        try:
            from panda3d.core import getModelPath as _get_model_path
            _get_model_path().append_path(str(_fixed))
        except Exception as _exc2:
            print('!! could not add %s to the panda3d search path (%s)'
                  % (_fixed, _exc2))
    elif _HERE != _picked and _picked not in _HERE.parents:
        # the old check, kept: the guess is not this folder and not any folder
        # above it, so it is somewhere unrelated entirely.
        print('assets: ursina guessed %s, which is not where this file is.\n'
              '        pinned to %s instead.' % (_picked, _HERE))
        application.asset_folder = _HERE
except Exception as _exc:
    print('!! could not check the asset folder (%s) - carrying on with %s'
          % (_exc, application.asset_folder))


GAME_FONT = 'comic.ttf'
try:
    from pathlib import Path as _P
    _fontdir = _P(str(application.asset_folder))
    _found = (_fontdir / GAME_FONT)
    if not _found.exists():
        _hits = list(_fontdir.rglob(GAME_FONT))
        _found = _hits[0] if _hits else None
    if _found:
        # this was a fix to a windows path bug, where if it can't find the comic.ttf font it will use the default.
        # panda3d does not use operating system paths.
        from panda3d.core import Filename as _Fn
        Text.default_font = _Fn.fromOsSpecific(str(_found)).getFullpath()
    else:
        _real_print('!! %s not found - the game will use the default font, download it from the internet for a better experience with the game : )'
                    % GAME_FONT)
except Exception as _exc:
    _real_print('!! could not set the font check the code (%s)' % _exc)


window.title = 'EternalMalice and Mercenary work'
window.color = color.black


# WINDOW SETTINGS - some tweakable options here to quickly make changes.
# I have no idea if this is gonna work for other computers the same!!! I REALLY HOPE SO.

NATIVE_RESOLUTION = True      # False = Ursina's own default window
# True  = launch filling the screen (borderless, any monitor, any resolution)
# False = launch in a window at WINDOWED_FRACTION of the screen
# F11 toggles either way, at any time.
START_FULLSCREEN  = False
# 1.0 = render at the monitor's real resolution. LOWER IT FOR SPEED: 0.8
# draws two thirds of the pixels and still fills the screen.
RESOLUTION_SCALE  = 0.6
WINDOWED_FRACTION = 0.65 # how much of the screen a windowed window actuuually uses
VSYNC = False  # OFF, deliberately - see the note below - i think for mac it might be useful to have it on
# honest comment I have NO IDEA if this works, i tried with 3 computers


def apply_window_mode():
    # HOW BIG IS THE SCREEN? Five ways to ask, first one that works wins.
    # window.screen_resolution - I could have also done this test with only this but for a failsafe for every different device
    # I did it like this to avoid annoying problems, so it checks what works.
    def _try_screen():
        yield lambda: (window.screen_resolution[0], window.screen_resolution[1])
        yield lambda: (window.fullscreen_size[0], window.fullscreen_size[1])
        yield lambda: (window.main_monitor.width, window.main_monitor.height)
        yield lambda: (window.monitors[0].width, window.monitors[0].height)
        yield lambda: (application.base.pipe.getDisplayWidth(), application.base.pipe.getDisplayHeight())
        yield lambda: (app.pipe.getDisplayWidth(), app.pipe.getDisplayHeight())

        yield lambda: (window.size[0] * 1.25, window.size[1] * 1.25)
    # i think this is overkill but as a last resort the last thing that ursina opened
    # will be scaled up by the 1.25 it divides the screen for its default windowed size with an equation.

    native, how = None, ''
    for i, getter in enumerate(_try_screen()): # main code on how it calculates the right resolution
        try:
            w, h = getter()
            if w and h and int(w) > 200 and int(h) > 200:
                native = Vec2(int(w), int(h))
                how = ('screen_resolution', 'fullscreen_size', 'main_monitor',
                       'monitors[0]', 'panda3d pipe', 'app pipe',
                       'window.size x1.25')[i]
                break
        except Exception:
            continue
    if native is None:
        print('could not work out the screen size by any means, because you dont have a native reolution, or its not accessible'
              'the window as Ursina made it, if you wish to change it please hard code your own resolution into the source code')
        return
    print('window: screen is %dx%d (found via %s)'
          % (native.x, native.y, how))

    # I had vsync off because it was messing with the fps of the game, but it ended up being
    # a complete other problem, the game wasn't deleting bullet assets after firing and was making the game filled with assets therefore lag like crazy.

    try:
        window.vsync = VSYNC
    except Exception as exc:
        print('!! could not change vsync:', exc)

    if not NATIVE_RESOLUTION:
        window.borderless = False
        print('native resolution disabled, using the default window')
        return
    # remembered so F11 can rebuild either mode without asking the driver again
    global SCREEN_SIZE
    SCREEN_SIZE = native

    # this guard stops 0.01 resolution scale. A scale under 0.35 is never what anybody really meant,
    # and silently clamping to 640x480 is how the window starts super small and not visable.
    scale = RESOLUTION_SCALE
    if scale < 0.35:
        print('!! RESOLUTION_SCALE is %.2f, which would make the window '
              'thats unusably small - using 1.0 instead' % scale)
        scale = 1.0

    try:
        set_window_fullscreen(START_FULLSCREEN, scale, native)
    except Exception as exc: # this is once again the failsafe i put in, so I could know what were the problems from my output right away.
        print('!! could not resize the window (%s) - it stays as it was' % exc)
        return

    mode = 'borderless fullscreen' if START_FULLSCREEN else 'windowed'
    print('window: %s on a %dx%d screen (scale %.2f, vsync %s)  -  F11 toggles'
          % (mode, native.x, native.y, scale, 'on' if VSYNC else 'off'))


SCREEN_SIZE = None            # filled in by apply_window_mode()
IS_FULLSCREEN = START_FULLSCREEN


def set_window_fullscreen(on, scale=None, native=None):
    global IS_FULLSCREEN
    native = native or SCREEN_SIZE
    if native is None:
        return
    if scale is None:
        scale = RESOLUTION_SCALE if RESOLUTION_SCALE >= 0.35 else 1.0

    if on:
        # RESOLUTION_SCALE IN FULLSCREEN
        # At 1.0 the window is exactly the screen max size
        want = Vec2(max(640, int(native.x * scale)),
                    max(480, int(native.y * scale)))
        window.borderless = True # native feature for ursina very convenient : )
        window.size = want
        window.position = Vec2(0, 0)
    else:
        want = Vec2(max(640, int(native.x * WINDOWED_FRACTION)),
                    max(480, int(native.y * WINDOWED_FRACTION)))
        window.borderless = False # also native feature for the engine
        window.size = want
        # centred by hand rather than by center_on_screen(), which is not on every ursina version, I am using not the latest, but one before the latest
        window.position = Vec2(max(0, int((native.x - want.x) / 2)),
                               max(0, int((native.y - want.y) / 2)))
    # keep ursina's own idea of the two sizes, so if anything else breakes in the engine it flips window.fullscreen it does not restore a 640x480
    try:
        window.fullscreen_size = Vec2(int(native.x), int(native.y))
        window.windowed_size = Vec2(max(640, int(native.x * WINDOWED_FRACTION)),
                                    max(480, int(native.y * WINDOWED_FRACTION)))
        window._fullscreen = bool(on)
    except Exception:
        pass
    IS_FULLSCREEN = bool(on)


apply_window_mode()

def RGB(r, g, b, a=255):
    if hasattr(color, 'rgba32'):
        return color.rgba32(r, g, b, a)
    return color.rgba(r, g, b, a)

HAND_IDLE_FILE = 'newhandNORM' #
HAND_GRAB_FILE = 'newhandWRD'


#DOOM TINKERING - all the shortcuts for doom level improvements

DOOM_FOLDER = 'DOOM_E1M1'          # main folder with the model of the map
DOOM_OBJ    = 'doom_E1M1.obj'      # main folder with the textures of the map - e1m1 means episode one map 1 from the original 1993 doom game
#I found the map asset remade online.

# The map is in DOOM units, and how far it's scaled has to agree with how tall
# the player is, therefore it was INCREDIBLY HARD AND ANNOYING to set everything up so the player
# seemingly is the same height in both levels the village and doom. The main problem was -
# that the DOOM files were very hard to scale down because originally they are huge.
# THE SCALING I MANAGED TO DO MYSELF, but later on for some doom features which I will point out I used AI again!


#the whole point of this is that everything is loaded in right as the game starts, but is hidden and situated  roughly on the same
#coordinates so, when levels change certain things get activated and certain do not, which is why the coordinates had to be
#scaled specific to every level

DOOM_CEILING_UNITS = 56          # DOOM's lowest walkable ceiling
DOOM_HEAD_MARGIN   = 0.40        # height roughly above your eyes
DOOM_SCALE_MIN     = 0.038       # the value that felt kind of right at eye height 1.75!
DOOM_ORIGIN = (1056, 2, -3616)
# This is the DOOM coordinate that becomes Ursina (0,0,0). This is E1M1's real
# player-1 start, so you spawn exactly where the player spawns.

# Where player appears in the level - for this I prompted AI to make me a code where everytime i press "T" in game
#show me the coordinates of where The player was currently, so I could calculate and mark down exactly where i wanted different attributes to be
#keycards, weapons, health packs, spawnpoints, NPC's, certain textures, doors a lot of stuff was made with this simple trick.
DOOM_SPAWN = Vec3(-48.98, 7.66, 14.69)

# If the wall textures come out upside down (because i exported it wrong from blender), flip this to True.
DOOM_FLIP_V = False

# DOOM's "F_SKY1" is not a real ceiling, it means "open sky above", it was not made in the asset, so Hiding it is the best option
# You can still see it in some parts of the map which I didn't fix, and if you jump out of the map
# fun fact - if you double jump above a ceiling unfortunately you can just jump out of the map ceiling.

DOOM_HIDE_SKY_FLATS = True

DOOM_SKY_TEXTURE = 'gridofdeath'
DOOM_SKY_SCALE   = 1.35     # multiplying the map's width, it must stay inside of the boundary box or it gets clipped away.

# This feature calculates metres per chunk of DOOM geometry, this Chunking exists so the graphics card can
# throw away pieces of the map that are off screen. On the village that is a big win, but with the resolution
# scaled down it does not matter as much - i have it pretty low on default, but a player can put it higher themselves in the code.
# these were the stats for doom_E1M1.obj:
#triangles in the whole doom map      1,820
#separate materials (textures)        57
#map size                             174 x 107 m
#if DOOM_CHUNK = 20 then 273 Entities = 273 draw calls a frame
#if DOOM_CHUNK = 0  then 57 Entities = 57 draw calls a frame

# 1,820 triangles split across 273 draw calls is SIX AND A HALF TRIANGLES PER DRAW CALL.
# The graphics card is not the problem of the slowing down - 1,820 triangles is nothing, it can handle much more
# the cost is the 273 separate submissions, each with its own texture change, done one at a time in Python
# and Panda3D before the graphics card running the game is even asked to do anything.

# And the culling was worthless here, because my view distance was so high: the map is 174m across, the DOOM view distance is 150m.
# so from most positions almost nothing was being culled anyway. I had 273 draw calls to save nearly nothing.

# 0 turns chunking off - one piece per material, which is the fewest possible without merging textures together.
# it is the single biggest thing in this file for DOOM.

# If the map would be much bigger than putting doom_chunk at 30/40 would start to matter, for a small map like this it does not.
DOOM_CHUNK = 0.0

# measured by PURE TRIAL AND ERROR BTW! took a stupidly long amount of time
OFFICE_DESK_TOP = 0.76        # the desktop surface, in metres

# the keyboard ends at z 1.16, the notebook at 1.30, and the lamp doesn't start until 1.47.
PHONE_POS     = Vec3(0.10, OFFICE_DESK_TOP + 0.005, 1.38)
PHONE_TEXTURE = 'store_control'      # the phone thats on the table and later in the players hand, the pack's tape recorder - reads as a handset

# The hand set in your hand during a call, in the hands own local space
# MEASURED OFF THE HAND MESH, not guessed - trial and error : )
PHONE_HELD_POS = Vec3(-0.85, -2.10, 2.30)
PHONE_HELD_ROT = Vec3(-6, -10, 6)
PHONE_HELD_SCALE = 0.55

# WHERE THE OFFICE STANDS IN THE APARTMENT ROOM, and where player starts.
OFFICE_ORIGIN_XZ = Vec2(-36.38, -4.32)    # the office
SPAWN_XZ         = Vec2(0.0, -3.2)        # player - see village_spawn_point() for more
OFFICE_GROUND_LIFT = 0.00                 # clearance above the floor minimum (had  this option because the table was spawning under the floor)
OFFICE_SPAWN = Vec3(SPAWN_XZ.x, 0.20, SPAWN_XZ.y)   # y replaced at load time

# not eto self - removed invisible box and the light
# A note on scale of a .glb - I mainly imported glbb files in the start because I didn't know how to make them into a blender file
# I only later realised i can make everything into a obj. - for easier scaling
OFFICE_DESK_OBJ   = 'officedesk.obj' # Office desk measurements and position in the starting level (apartment)
OFFICE_DESK_SCALE = 1.0
OFFICE_DESK_POS   = Vec3(-0.20, 0.0, 0.30)
OFFICE_DESK_ROT   = Vec3(0, 0, 0)

# One texture per object group - the .obj carries a usemtl per object.
# HOW TALL THE PILLARS ARE, in metres above the office
# I made this so the player wouldn't clip onto the table in the apartment, I just made a huge collider so the player wouldn't clip over it
#but then I had to exclude the collider so the player could still interact with the phone on the table
NO_CLIMB_TOP = 6.0
# Every one of those invisible pillars, so the interact raycast can ignore them
# otherwise they stand between you and the phone. !!!See do_interact().!!!
#
no_climb_boxes = []

# REMOVE LATER! NOTE TO SELF THIS IS NOT NEEDED
OFFICE_SCREEN_ON      = True
# removed the spreadshet infront of office screen - looked horrible
# None means the screen quad is never built at all - not built and hidden,
OFFICE_SCREEN_TEXTURE = None

OFFICE_SCREEN_POS     = Vec3(0.316, 1.146, 0.531)
OFFICE_SCREEN_YAW     = 90
OFFICE_SCREEN_SIZE    = (0.42, 0.42)

OFFICE_SCREEN_UNLIT   = True

#All textures for office desk, not all are even used
OFFICE_DESK_TEXTURES = {
    'Table_Rough': 'tex_table',      'Chair':            'tex_chair',
    'Clipboard':   'tex_paper',      'Notepad':          'tex_paper',
    'Notebook':    'tex_paper',      'Computer':         'tex_computer',
    'Monitor':     'tex_computer',   'Screen':           'tex_computer',
    'monitor':     'tex_computer',   'Keyboard':         'tex_computer',
    'Computer_Mouse': 'tex_computer', 'Ashtray':         'tex_smokes',
    'Ashtray_Ash': 'tex_smokes',     'CigarettePack_Blue': 'tex_smokes',
    'Cigarette_Normal': 'tex_smokes', 'Lamp01':          'tex_lamp',
    'Microphone':  'tex_lamp',       'Cactus_Pot':       'tex_cactus',
    'Phone':       'tex_phone',      'Cactus':           'tex_cactus',
}
# built once, lowercased, so 'Monitor' / 'monitor' / 'MONITOR' all resolve and work, very useful code : )
OFFICE_DESK_TEXTURES_CI = {k.lower(): v for k, v in OFFICE_DESK_TEXTURES.items()}

# The old cubicle .glb. Kept, so one flag switches back. - this is the Office model entirely itself
OFFICE_USE_DESK_SET = True
OFFICE_GLB       = 'office_lowpoly'
OFFICE_GLB_SCALE = 0.62 # i didn't really have anything figured out at this point yet so just finding the correct scale took hours : )
OFFICE_GLB_POS   = Vec3(-1.05, -0.08, 2.30)
OFFICE_GLB_ROT   = Vec3(0, 180, 0)  

OFFICE_ORIGIN_XZ = Vec2(0.0, 0.0)      # dead centre of the village
OFFICE_FACING    = 90                 # office turned a bit so the chair would be inthe correct place
SPAWN_OFFSET     = Vec3(0, 0, -3.2)    # you stand this far in front of it

#Overpowered weapon i rndomly wanted to add - as a reward for wandering around the map.
ANGLER_GLB = 'heavy_angler'
ANGLER_GLB_SCALE = 1.5

OFFICE_BOX_HALF   = Vec2(6.0, 6.0)   # metres either side of the office centre
OFFICE_BOX_FADE   = 6.0              # metres of softening at the boundary
OFFICE_FADE_SPEED = 1.6              # lower = slower, gentler crossfade - completely useless old feature:>
# the DESK_DARK settings that were here are gone, along with the code that used them.


PLAYER_MAX_HP = 400 # might be too little, the enmies are kind of strong

# EYE HEIGHT, PER SCENE.
# Every FPS tutorial that i found said to make differnet heights for differnet maps - i think this is actually
# only useful when you care about the textures and models and keeping them consistent, so it's actually not that important: the camera height is a property to be changed
PLAYER_HEIGHT = 1.75     # DOOM, and the fallback for anything unlisted
EYE_HEIGHT = {
    'office':  1.60,
    'apartment': 1.60,   #  the rented room
    'throne':    1.60,   #  the throne room ending
    'djhouse':   1.60,   # the DJ's garden
    'doom':    1.40,     # normal FPS height
    'finale':  1.55,
    'ending':  1.70,
    'house':   1.60,     # inside the five NPC houses
    # as I am editing this when the game is finished - this was a complete waste of time : )
}
HOUSE_SPEED = 3.4        # walking pace indoors
OFFICE_SPEED  = 3.0
WORLD_SPEED   = 5.4      # outside, where there's somewhere to actually go

OFFICE_SLOWS_YOU = False
DOOM_SPEED    = 5.0      # was 9.0, which was a sprint at this eye height

#  whatever eye height the player chooses (assuming anyone would edit the code), the DOOM ceiling
# stays above your head. Printed at startup so you can see what it landed on.
DOOM_SCALE = max(DOOM_SCALE_MIN,
                 (PLAYER_HEIGHT + DOOM_HEAD_MARGIN) / DOOM_CEILING_UNITS)

# Sprint, crouch and lean, working the same way in every scene.
SPRINT_MULT   = 1.85
CROUCH_MULT   = 0.42
CROUCH_HEIGHT = 0.95     # eye height while crouched

# I had a leaning mechanic but it was just useless, although i liked the idea of it.
LEAN_ENABLED  = False
LEAN_ANGLE    = 10       # degrees of roll
LEAN_SHIFT    = 0.30     # how far the camera slides sideways
LEAN_SPEED    = 9        # how quickly it gets there
BOB_SPEED     = 12.5      # footstep bob while walking
BOB_AMOUNT    = 0.095


# Ursina's controller can only step up 0.5 units by itself. DOOM stairs go up
# in 8 / 16 / 24 unit chunks and 24 * 0.038 = 0.91, so we help it along!!
MOUSE_SENS  = Vec2(40, 40)
STEP_HEIGHT = 0.95

JUMP_HEIGHT      = 1.1     # the normal hop, everywhere
DOOM_JUMP_MULT   = 1.5     # DOOM gets one and a half times that
DOUBLE_JUMPS     = 1       # extra jumps once you're airborne. 2 = triple jump, very fun.
# ONLY THE DOOM LEVELS GET THE DOUBLE JUMP
# The village, your flat, the five houses and the throne room are places you can't double jump
DOUBLE_JUMP_SCENES = {'doom'}
# HOW HIGH THE SECOND JUMP GOES
# 2.25 x 1.5 = 3.375
DOUBLE_JUMP_HEIGHT = 3.375   # metres of rise. Was 2.25, x1.5 as asked.


# HALF-LIFE 2 ARMS
HANDS_USE_HL2 = True

if HANDS_USE_HL2:
    HANDS_FOLDER = 'hl2hands'
    HANDS_OBJ    = 'v_hands.obj'
else: # if they wouldn't load or seomthing would be missing
    HANDS_FOLDER = 'hands'
    HANDS_OBJ    = 'full.obj'


# full.obj ships without its .mtl, so the materials are matched to textures by
# name prefix here instead. defaultMat.001/.002 -> skin, Material.001/.002/.003, this was due to me using this asset
#from the in ternet and it now having conrete texture files out so it was just material1,2,3,4
HANDS_USE_BODY_TEXTURE = True
HAND_MATERIAL_TEXTURES = {
    'defaultMat':   'defaultMat_Base_color',
    'Material':     'bands_Base_color',
    'v_hand_sheet': 'v_hand_sheet',             # HL2's arms
}

# Where the hands sit relative to your eyes.
# z is forward, y is up, so a negative y means "below the eye line", which is what I want for my arms
if HANDS_USE_HL2:
    # v_hands.obj measures 32 x 24 x 23 with its origin ABOVE the wrists roughly according to the asset model
    # (Y runs -30.8 to -6.8), which is how Valve rigs a viewmodel also
    HANDS_SCALE   = 0.080
    HANDS_POS     = Vec3(0, -2.0, 0.55)
    HANDS_ROT     = Vec3(280, 0, 2.4)
    HANDS_POS_GUN = Vec3(0, -0.76, 0.58) # this tinkering took like 3 days :---
    HANDS_ROT_GUN = Vec3(212, 0, 0)
    # On the phone: arms come up and turn in, so the handset ends up beside your head instead of held out in front of the players chest
    HANDS_POS_PHONE = Vec3(-0.06, -2.0, 0.52)
    HANDS_ROT_PHONE = Vec3(280, 9, 2.4)
    HANDS_MIRROR  = False
    HANDS_SPREAD  = 0.11       # tinkerable should be a bit longer maybe
else:   #if hands dont load or anything goes wrong
    HANDS_SCALE   = 0.90
    HANDS_POS     = Vec3(0, -0.44, 0.58)
    HANDS_ROT     = Vec3(85, 0, 0)
    HANDS_POS_GUN = Vec3(0, -0.54, 0.64)
    HANDS_ROT_GUN = Vec3(95, 0, 0)
    HANDS_POS_PHONE = Vec3(-0.10, -0.40, 0.52)
    HANDS_ROT_PHONE = Vec3(80, 14, 0)
    HANDS_MIRROR  = True
    HANDS_SPREAD  = 0.16

# here i drew the hands in their own pass so nothing can ever cover them - not walls,
# not your own chest. Set False to go back to a plain look - this was suuuuper helpful because other textures kept going over the hands.
HANDS_OWN_DEPTH_LAYER = True

#bobbing for a more realistic look, i tried my best hehe...
HANDS_BOB_SPEED  = 15.0     # steps per second-ish
HANDS_BOB_AMOUNT = 0.044   # walking swing, was 0.034
HANDS_SWAY       = 0.032   # how much they lag behind the mouse
HANDS_BREATHE    = 0.075   # IDLE up/down, was 0.030
# degrees of rock, driven by the SAME step clock as the bob so a foot landing,
# the camera dipping and the arms rolling all happen on the same beat
HANDS_BOB_ROLL   = 2.6     # side-to-side rock, one per step
HANDS_BOB_YAW    = 1.7     # a small turn in and out with it
HANDS_BOB_PITCH  = 1.4     # and a nod on each footfall

# THE HAND SCALE IS  WIRED TO THE BOB. Each footstep the whole viewmodel
# breathes in size by this fraction, in time with the swing
HANDS_SCALE_PULSE = 0.032      #was 0.01 before and 0.022

# Which scenes get bob/sway/breathe at all.
# The office and the houses are IN now, so the arms move
HANDS_MOTION_IN = {'office', 'doom', 'finale', 'house'}

BODY_MODEL   = 'Adam'
BODY_TEXTURE = 'fulltemplate model'   # texture for Adam.obj
BODY_COLOR   = RGB(214, 178, 156)   # same skin tone as the hand model
SHOW_BODY    = True       # set False if it gets in the way, otherwise its good
BODY_OWN_DEPTH_LAYER = True

# eyes are at the FRONT of your head, not the middle of it. Without this the neck and shoulders sit directly under the camera and swallow the bottom
BODY_OFFSET = Vec3(0, 0, -0.38)

# Adam is 13.33 model units tall according to ursina, with his feet at 0. Human eyes sit at about  94% of total height, and the camera is at PLAYER_HEIGHT, so the body has to
BODY_MODEL_HEIGHT = 11.33
# A real person is about 1.8m whatever you set the camera to. This used to be
# be derived from PLAYER_HEIGHT, which meant raising  eye height also inflated a bit
BODY_REAL_HEIGHT = 2.0
BODY_SCALE = BODY_REAL_HEIGHT / BODY_MODEL_HEIGHT

# The head is KEPT the same. Cutting it open left the player staring down into a hollow torso,
# which looked far worse.
BODY_CUT_ARMS  = True
BODY_ARM_CUT_X = 1.85     # anything further out sideways than this is cut
BODY_ARM_CUT_Y = 5.0      # and higher up than this, is an arm so cut

# Two separate problems, two separate fixes for this issue
# THINGS POKING THROUGH IT, poking through the model
BODY_ON_VIEWMODEL = True    # always on top
BODY_DOUBLE_SIDED = True    # no angle can see through it
BODY_CUT_HEAD     = True    # remove everything above the camera
BODY_CUT_TOP_Y    = 8.4     # model units - see above

# Adam is a static mesh with no skeleton so i couldnt rig it up in blender, so the legs cannot literally swing.
# What Cruelty Squad and the PS1 Silent Hills also do on screen, though, is just create a rock
BODY_WALK_ROCK  = 4.5    # degrees of side-to-side roll (weight onto each leg)
BODY_WALK_TWIST = 7.0    # degrees of hip twist per step (Cruelty Squad swagger)
BODY_WALK_DIP   = 0.045  # metres the body sinks at each footfall
BODY_WALK_LEAD  = 0.03   # metres it leans forward while moving
# This is the standard "procedural viewbob on a static mesh" trick - the same
# pattern as ursina's own smooth_follow + the head bob in mandaw2014's FPS which I used some of the code of

# 1. I accidentally rigged something up falsely so the FOG_VILLAGE_COLOR is NOT fog, despite the name. It is the colour of the
#    SKY SPHERE - cemetery_sky.color reads it, and the sky cycler rewrites it every time the sky texture changes.
#    Keeping the old name so the sky code still finds it.
# 2. The FINALE still has fog, and it is the good one - black fog closing in
#    while the player has the finale text. That is the only place it is still switched on.
FOG_VILLAGE_COLOR = RGB(104, 106, 116)
FOG_FINALE = (10.0, 20.0)          # the confrontation, and only that
FOG_SCENES = {'office', 'finale'}  # which scenes are allowed fog at all

# the lamp on the office desk - this one is ON
OFFICE_LAMP = True

# the sky ball has to sit inside CLIP_FAR['office'] or it gets clipped away
SKY_RADIUS = 26.0

# HOW FAR YOU CAN SEE, per scene. Past this the camera draws literally
# nothing, which is free framerate - there is no point drawing the far half
# of the village when you are stood in a doorway looking at a wall.
# I tuned each of these by walking around and lowering it until I noticed.
CLIP_FAR = {
    'apartment': 40.0,   # one room, nothing to see past it anyway
    'throne':    36.0,   # a twelve metre hall.
    'djhouse':   50.0,   # a garden, so you want to see across it
    'office': 31.0,      # was 34, and 46 and 95 before that - kept coming down
    'house':  60.0,
    'doom':   120.0,     # E1M1 is about 115m across, so this still shows the
                         # whole map from any corner of it
    'finale': 60.0,
    'ending': 1500.0,    # the garden is the one place that wants a horizon
}

# THE WALL COLLIDERS ARE SWITCHED ON AND OFF AS the player WALKS
# There are about 1300 invisible collision boxes making up the village walls.
# Having all of them switched on at once is genuinely expensive, and you can
# only ever bump into the ones near you - so only those are on.
WALL_COLLIDER_RADIUS = 30.0    # was 16.0, and 16 was close enough to sprint
                               # past a wall before it turned solid
WALL_COLLIDER_TICK   = 0.40    # how often it re-checks, in seconds

#ranodm fact - with the tick being this high, its possible to clip through walls by lowering your framerate : )

# and how many are allowed to change in ONE tick. Without this, arriving in
# the village switched about forty boxes on in a single frame and you felt it
# as a hitch. Spreading them over a few frames is invisible.
WALL_SWITCH_BUDGET   = 12

# the village mesh is cut into squares this big so the ones behind you can be
# skipped entirely. Smaller = more pieces but better skipping.
VILLAGE_CHUNK = 12.0

# the five houses nearest the office are the ones that get a real door
HOUSE_COUNT          = 5

# where the houses actually are. This is measured off the model and saved to
# a file rather than guessed at startup - guessing is what used to put the
# doors and the textures on the wrong buildings.
#I didnt end up using it much, I was gonna have a crazy village texturing file to change all of the houses to be crazy textures as well, but
#I honestly didn't have time for it

HOUSE_DATA_FILE      = 'village_houses.json'

# only used if that file is missing, as a last resort so the game still runs.
# It tries to find houses by clustering the collision boxes, which is much
# worse - see pick_house_boxes().
HOUSE_CLUSTER_GAP    = 0.6
HOUSE_MIN_SIZE       = 3.0
HOUSE_MAX_SIZE       = 40.0
HOUSE_MIN_HEIGHT     = 2.2

# NOTHING HERE IS RANDOM, on purpose. Each house takes its textures BY INDEX
# out of these lists, so house 1 always looks like house 1. Play it a hundred
# times and the street is identical, which is what I wanted.
HOUSE_WALL_TEXTURES  = ['suburb_brick_1', 'suburb_brick_2', 'randomrainbow',
                        'ribcage', 'red_marble']
HOUSE_TRIM_TEXTURES  = ['store_progress (1)', 'store_freedom', 'store_control']
# no longer in the game : )

# the five doors, in street order, matched to who is behind each one:
#   1 organ seller   2 the scientist   3 the weird one   4 the DJ   5 players
HOUSE_DOOR_TEXTURES  = ['grandma1new', 'grandma2new', 'grandma3',
                        'container_lime_endnew', 'grandma4']
HOUSE_DOOR_ROOM = [1, 0, 2, 3, 4]

# how far the door panel floats off the real wall, so it does not z-fight
# with the painted-on door underneath it
HOUSE_SKIN_INSET     = 0.06

# WHERE THE FIVE DOORS ACTUALLY GO.
# This was the thing that finally worked. I tried finding the houses by
# measuring the model and by clustering the collision boxes, and both of them
# kept putting doors on the wrong buildings or halfway through a wall.
# So instead I just walked around the village in game, stood in front of each
# house, and pressed P to print my own coordinates. and madea  door and spawnpoint for the player
HOUSE_DOOR_POSITIONS = [
    Vec3(-21.13, -0.32,  6.26),    # 1  the organ seller
    Vec3(-32.37, -0.32,  6.26),    # 2  the scientist
    Vec3(-35.46, -0.61, -6.31),    # 3  the weird one
    # door 4 took me two goes. My first coordinate was about half a metre
    # further into the house and lower, which buried the door INSIDE the wall
    # - so the interact ray hit the house before it ever reached the door and
    # pressing E did absolutely nothing.
    Vec3(-46.50, -0.11, -6.21),    # 4  the DJ
    Vec3(-56.00,  0.06,  6.02),    # 5  the one you buy at the end
]

# which way each door faces, in degrees. None means work it out for me, which
# is "turn to face the road" - the street runs along x at about z = 0, so a
# door at z = +6 faces backwards and one at z = -6 faces forwards. That got
# all five right so I never had to type an angle in.
HOUSE_DOOR_YAW = [None, None, None, None, None]

# doors that need another door visited first. It is empty now - nothing in the
# village is locked behind talking to somebody any more.
HOUSE_LOCKED_UNTIL = {}

# the last house is the one you BUY or more of like collect, so it stays shut until the DOOM job is
# finished and an ending has actually played. Walking up to it early just tells you off.
DOOR5_NEEDS_CAMPAIGN = True
DOOR5_LOCKED_MESSAGE = 'you are poor, finish the job'
HOUSE_LOCKED_MESSAGE = 'get a job'
HOUSE_FORSALE_DOOR = 4

ENDING_EXPLORE = True        # False = roll the credits instead of letting

# an older way of placing doors, one per house, kept only because the fallback
# path still mentions it. HOUSE_DOOR_POSITIONS above always wins.
HOUSE_DOOR_OVERRIDE = {
    # 0: Vec2(-3.18, 4.45),      # example: house 1's door
}

# the doors are deliberately twice as tall as a real door - 4.2m. They are
# placed by their FLOOR, so making them taller grows them upward and the
# bottom stays on the ground. Looks wrong in a screenshot, reads fine in game. also its kinda funky and funny
HOUSE_DOOR_SIZE      = (1.4, 4.2)   # metres

# EVERY DOOR IS E ONLY NOW. Walking into them used to open them, and that
# kept grabbing me while I was just squeezing past on the street, which was
# infuriating. Leaving the setting here in case I ever want it back.
DOOR_WALK_IN         = False
HOUSE_WALK_IN_RANGE  = 1.4     # only means anything if DOOR_WALK_IN is True
INTERACT_RANGE       = 4.5     # how far E reaches, for everything in the game
PHONE_REACH_RANGE    = 4.2
HOUSE_NUMBER_SCALE   = 14      # the floating 1..5 sign over each door
HOUSE_NUMBER_LIFT    = 0.70    # metres above the top of the door

# THE DOORS INSIDE THE HOUSES - the ones you press E on to get back out.
# Every room needed its own height because the ceilings are all different and
# a door taller than the ceiling pokes out through the roof from outside.
ROOM_EXIT_DOOR_WIDTH  = 1.2       # same width as the five street doors
ROOM_EXIT_DOOR_HEIGHT = {
    0: 2.00,     # the horror corridor - only 2.1m over the top landing
    1: 2.40,     # the shop, 2.87m ceiling
    2: 2.60,     # Jake's room, 3.2m ceiling. Was 4.2 and it went through it
    3: 2.60,     # the DJ's garden, outdoors so it does not matter much
    4: 2.40,     # the spare room
}
ROOM_EXIT_DOOR_HEIGHT_DEFAULT = 2.40
# if a room has no door picture of its own it wears this one
ROOM_EXIT_DOOR_FALLBACK_TEX = 'Loser0'

# HOW SHARP THE TEXTURES ARE. This is the biggest speed dial in the game and
# it is also the most PS1 thing in it - low detail is not a compromise here,
# blurry chunky textures are the look I wanted.
TEXTURE_DETAIL_LEVELS = {
    'ultra':  1.00,
    'high':   0.75,
    'medium': 0.50,
    'mid':    0.35,
    'low':    0.25,
    'potato': 0.10,      # every texture at a tenth. Genuinely playable.
    'costom': 0.20,
}
TEXTURE_DETAIL = 'costom'      # change this one word to change the whole game DONT DO IT THE GAME IS SO POORLY OPTIMISED
# IF YOU CHANGE IT THE GAME MIGHT BE UNPLAYABLE DUE TO FPS - but you can see the t extures better yes

# or say it on the command line instead: python launcher.py mid
# THIS HAS TO BE HERE and not at the bottom of the file, which is where it used
# to be - every texture in the game is already loaded by then, so asking for
# potato down there only changed the number in the startup line
for _arg in sys.argv[1:]:
    _want = str(_arg).strip().lower().lstrip('-')
    if _want in TEXTURE_DETAIL_LEVELS:
        TEXTURE_DETAIL = _want
        print('textures: %r asked for on the command line' % _want)


# some things have to ignore the setting above - a full screen picture at a
# quarter resolution looks like a mistake rather than a style. This number
# cancels the global one back out for those.
FULL_DETAIL = 1.0 / max(0.01, TEXTURE_DETAIL_LEVELS.get(TEXTURE_DETAIL, 1.0))
TEXTURE_MIN_PX = 1            # never shrink a picture smaller than this

# THE LITTLE CROSS THAT FLASHES WHEN YOU HIT SOMETHING.
# Four small ticks around the crosshair. White for a hit, bigger and red for
# a kill, so you can tell the difference without looking at the health bar.
HITMARKER_ON        = True
HITMARKER_SIZE      = 0.020    # fraction of the screen, per tick
HITMARKER_GAP       = 0.016    # how far the four ticks sit from the middle
HITMARKER_TIME      = 0.10     # seconds it stays up for an ordinary hit
HITMARKER_KILL_TIME = 0.30     # a kill hangs around longer so you notice
HITMARKER_COLOUR    = RGB(255, 255, 255)
HITMARKER_KILL      = RGB(255, 60, 50)
HITMARKER_KILL_SCALE = 1.3     # a kill marker is this much bigger
HITMARKER_SOUND     = True

# tracers are OFF. Each pellet used to make its own little flying line, and a
# shotgun fires seven of them, so one trigger pull was seven new objects made
# and thrown away - that was a real stutter every time I fired.
BULLET_TRACERS = False
# the spark where the shot lands stays, because it is one per SHOT rather
# than one per pellet, and they are reused from a pool instead of made fresh.
BULLET_SPARKS = True


# THE BOSS DEATH SCENE
CEO_DEATH_DELAY   = 3.0        # seconds between him dying and the fade
CEO_FADE_TIME     = 1.2        # how long the fade to black takes
# fullscreen, because at 0.62 height and shoved to the left they read as a
# picture stuck on the screen rather than the ending itself
CEO_PICTURE_FULLSCREEN = True
CEO_PICTURE_HEIGHT = 0.62      # only used if FULLSCREEN is False
CEO_PICTURE_POS   = (-0.28, 0.02)   # same, ignored while fullscreen is on
# three pictures, shown in turn while the ending text runs
CEO_PICTURES = ['lifepictureENDING', 'ceo_of_the_universe', 'bossending']
CEO_PICTURE_SWAP = 6.0         # seconds each one is up before the next
CEO_BUTTON_IMAGE  = 'controlredfinal'
CEO_BUTTON_HEIGHT = 0.26
CEO_BUTTON_POS    = (-0.28, -0.40)
CEO_BUTTON_HINT   = 'click to go back'
# i think this doesnt work properly yet

# THE THRONE ROOM - the room behind door 5, the one you buy.
ROOM_THRONE_MESH_COLLIDER = True

ROOM_THRONE_GRID    = 1.0
ROOM_THRONE_STAND_MAX = 2.6

ROOM_THRONE_WALLS   = True
ROOM_THRONE_WALL_PAD = 0.15
ROOM_THRONE_UNLIT   = True
ROOM_THRONE_SPEAKER = ''

# YOUR FLAT VERY MESSED UP. The room the whole game starts and ends in.
#THERES JUST A LOT OF RANDOM STUFF HERE FOR THE STORY
APARTMENT_AT      = Vec3(300, 0, 300)     # parked away from everything
# 4.8m tall, which is far too tall for a bedroom - but the door is the same
# 4.2m door as the village uses and it has to fit through the wall.
APARTMENT_SIZE    = (9.0, 4.8, 7.5)       # width, height, depth in metres
APARTMENT_WALL    = 'weaponsguns'
APARTMENT_FLOOR   = 'Crumbfloor'
APARTMENT_CEILING = 'watchtimeMEME'
APARTMENT_CEILING_FALLBACK = 'ceiling'
APARTMENT_CEILING_TILE = (1, 1)   #
APARTMENT_WALL_TILE  = (3, 2)     # how many times the wall texture repeats
# the floor IS a tiling texture rather than a picture, so it repeats. 6x5 over
APARTMENT_FLOOR_TILE = (6, 5)
# THE BED. Coordinates read in game with P and typed straight in here BASICALLY
APARTMENT_BED_ON    = True
APARTMENT_BED_GLB   = 'hospital_bed'    # this one carries its own textures
APARTMENT_BED_AT    = Vec3(-2.175, 0.0, 2.73)   # relative to the room
APARTMENT_BED_YAW   = 90                # turned so it lies along X
APARTMENT_BED_SCALE = 1.15              # 1.774 x 1.15 = 2.04m long, about right

# the desk set, in the middle of the room, turned so the chair faces the door
APARTMENT_DESK_POS = Vec3(0.4, 0.0, 0.6)
APARTMENT_DESK_ROT = 180
# where you wake up, and which way you are looking
APARTMENT_SPAWN = Vec3(-2.6, 0.25, -2.2)
APARTMENT_FACE  = 40
# THE FRONT DOOR. It is on the -z wall inside, and it comes out into the
# village at the coordinates below, which I read off in game rather than
# calculating. The same door exists on both sides so it lines up.
APARTMENT_DOOR_ON_Z = -1          # -1 = the -z wall, +1 = the +z wall
APARTMENT_DOOR_X    = 2.4         # how far along that wall it sits
APARTMENT_EXIT_TO   = Vec3(-3.66, 0.57, -31.94)   # where the door is outside
# and where you actually STAND when you come out. This used to be worked out
# as "the door minus 1.6 metres", which kept landing me half inside the wall,
# so now it is its own coordinate that I stood on and printed.
APARTMENT_STEP_OUT  = Vec3(-3.02, -0.08, -30.17)
APARTMENT_EXIT_FACE = 0           # which way you are looking when you step out
APARTMENT_DOOR_TEX  = 'Loser0'
APARTMENT_DOOR_SIZE = HOUSE_DOOR_SIZE

#rent notice picture,a flat picture in Ursina faces one particular way at rotation 0, and it is drawn on
# both sides, so putting it on the wrong wall shows you a mirrored copy rather
# than nothing, which took me a while to notice.
APARTMENT_RENT_WALL      = 's'
APARTMENT_RENT_WALL_AT   = -2.2         # how far along that wall
APARTMENT_RENT_WALL_LIFT = 1.70         # how high up
APARTMENT_RENT_WALL_SIZE = (0.80, 1.04)

# EVERYTHING ON THE WALLS, as (picture, wall, along, height, size).
# the wall letters are: 'n' = -z, 's' = +z, 'w' = -x, 'e' = +x
APARTMENT_PICTURES = [
    ('controlredfinal', 'w', -1.4, 1.75, (1.5, 1.5)),
    ('house100',        'w',  1.4, 1.75, (1.5, 1.5)),
    ('watermark',       'e',  0.0, 2.10, (2.6, 0.29)),
    # sits directly under the watermark - that is 2.6 x 0.29 hung at 2.10, so
    # its bottom edge is at 1.955 and this one starts just below it
    ('2ac1d15a38c5b17be7458c43efaa5967', 'e', 0.0, 1.28, (1.20, 1.29)),

    # human supremacy, on the walls of the room you rent, which I thought was
    # funny, also related to the story. The picture is 1408 x 642
    ('humanSUpremacy', 'n', -1.60, 2.60, (2.19, 1.00)),
    ('humanSUpremacy', 's',  1.60, 2.35, (2.19, 1.00)),

    # the face, high up on the west wall above the other two
    ('memeface', 'w', 0.0, 2.75, (0.90, 0.91)),

    # THE LATE RENT NOTICE, three times, on three different walls, so whichever
    # way you turn when you wake up there is one in front of you
    ('laterent', APARTMENT_RENT_WALL, APARTMENT_RENT_WALL_AT,
     APARTMENT_RENT_WALL_LIFT, APARTMENT_RENT_WALL_SIZE),
    ('laterent', 'n',  1.15, 1.55, (0.95, 1.24)),
    ('laterent', 'e', -1.90, 2.05, (0.62, 0.81)),
    ('grinchsultimatum', 'w',  0.0, 1.62, (1.46, 0.80)),
]
# and a fourth copy of the rent notice lying on the desk itself
APARTMENT_RENT_TEXTURE = 'laterent'
APARTMENT_RENT_POS  = Vec3(0.72, OFFICE_DESK_TOP + 0.005, 1.16)
APARTMENT_RENT_SIZE = (0.30, 0.39)      # metres, so about A4
APARTMENT_RENT_TURN = 11                # turned a bit so it looks dropped
                                   # looks horrible im gonna be honest literally floating

OFFICE_IN_APARTMENT = True   # the desk lives in the flat now, not outdoors

# EVERY SCALE BELOW IS MEASURED, NOT GUESSED. I opened each model first and
# printed its real size, and the numbers it gave are left in the comments so
# I can tell whether a scale is right without opening the file again.
ROOM_JAKE_GLB   = 'vandalized_room'
ROOM_JAKE_SCALE = 3.2 / 96.0
# at the raw size it was genuinely the size of a car, this sscaling was very annoying
ROOM_JAKE_TOILET_GLB   = 'dirty_toilet'
ROOM_JAKE_TOILET_SCALE = 0.78 / 8.51
ROOM_JAKE_TOILET_YAW   = -35     # turned a bit so it looks dumped there

# all of these I printed in game, so they are WORLD positions rather than
# positions inside the room. Easier than working out room-relative numbers.
ROOM_JAKE_NPC_WORLD    = Vec3(898.18, 0.00, -597.13)
ROOM_JAKE_TOILET_WORLD = Vec3(901.15, 0.00, -597.24)
ROOM_JAKE_EXIT_WORLD   = Vec3(900.69, 0.00, -608.22)
# I SPAWNED ON THE CEILING IN HERE and the coordinate was not the problem.
# The spawn code fires a ray straight down to find the real floor, and in this
# room the first thing below me was the ceiling of the floor below, so it put
# me on top of that. The y of 0.01 keeps me under it.
ROOM_JAKE_SPAWN_WORLD  = Vec3(900.92, 0.01, -606.19)
ROOM_JAKE_FACE  = 0
# 180, not 0. A flat picture in Ursina faces -z at rotation 0, and I stand on
# the +z side of this door - so at 0 I was being shown the BACK of the door
# picture, which just looks like a blank panel.
ROOM_JAKE_EXIT_YAW = 180
# Jake faces 0, not 180 like everybody else. The 180 is correct for the .glb
# models because Ursina flips their Z when it loads them - but Jake is an .obj
# and does not get flipped, so giving him the same 180 turned him around and
# he stood with his back to me the whole conversation.
NPC_JAKE_YAW = 0

# JAKE. The model is 22.77 x 73.55 x 14.65 in its own units - that is roughly
# 0.31 wide for every 1 tall, which is a person-shaped ratio, so I can just
# scale him to a height and trust it.
NPC_JAKE_OBJ    = 'gmanJAKE'
NPC_JAKE_HEIGHT = 1.75
NPC_JAKE_TEXTURES = {
    'dc_gman_head.BMP':      'memeface', # the model is orignally gman from half life 1, which is why the asset is named like this here
    'dc_gman_head_top.BMP':  'nerves',
    'dc_gman_body.BMP':      'Enemy_Security2',
    'dc_gman_coat.BMP':      'ribcage',
    'dc_gman_cuff.BMP':      'red_marble',
    'dc_gman_briefcase.BMP': 'humanSUpremacy',
}

# THE THRONE ROOM. This model measures 12.00 x 5.90 x 12.20 and is ALREADY IN
# METRES, which almost nothing else in this project is - so its scale is 1.0
# and I did not have to work anything out. Rare and amazing
ROOM_THRONE_GLB   = 'throne_room'
ROOM_THRONE_SCALE = 1.0
ROOM_THRONE_AT    = Vec3(-500, 0, 500)   # parked far away like every room
ROOM_THRONE_SPAWN = Vec3(-0.05, 0.60, 2.63)      # printed in game with P
ROOM_THRONE_FACE  = 0
ROOM_THRONE_EXIT  = Vec3(0.01, 0.0, 4.44)        # same
ROOM_THRONE_EXIT_YAW = 0

# THE THRONE ROOM IS A DELIBERATE MESS OF TEXTURES.
# should look like the room is wrong rather than like the room is decorated.
ROOM_THRONE_CHAOS = True
ROOM_THRONE_CHAOS_SKINS = [
    'ribcage', 'guts', 'nerves', 'red neck together', 'randomrainbow',
    'red_marble', 'Enemy_MegafuckElite2', 'Enemy_Security2', 'Enemy_Orange',
    'eye 1', 'eye 2', 'greenieface', 'greeter_face', 'funko', 'grandma',
    'grandma2', 'grandma3', 'crungewallpaper', 'purple_carpet', 'menunaked',
    'laterent', 'watchtimeMEME', 'randomExcelsheetMEME', 'cover_edit_heavy',
    'Jasper imageORDER', 'afterwork_skin', 'humanSUpremacy', 'memeface',
    'monthlysubscription', 'perfectbody', 'lifecourse', 'house100',
]
# the tiling numbers are deliberately ugly and prime-ish - 11 x 1, 2 x 9 -
# because neat numbers like 2 x 2 look like a floor and these look broken
ROOM_THRONE_CHAOS_SCALES = [(1, 1), (3, 2), (2, 7), (11, 1), (1, 5), (5, 5),
                            (13, 3), (2, 9), (7, 2), (4, 11)]
# the problem with this room is it only HAS one material, so splitting by
# material would just paint the whole thing one colour. So it gets cut into
# cubes this many metres across instead, and each cube gets its own picture.
ROOM_THRONE_CHAOS_CHUNK = 6.0
ROOM_THRONE_KEEP = 0.45


ROOM_DJ_GLB   = 'village_house_lowpoly'
ROOM_DJ_GRASS = 'Material'          # the grass, found exactly like that

ROOM_DJ_SKINS = {
    'Material':    ('GrassBrown',        (6, 6)),    # the ground
    'Material_1':  ('darkwood',          (3, 3)),
    'Material_2':  ('suburb_brick_1',    (2, 2)),
    'Material_3':  ('Dedinaru5b',        (2, 2)),
    'Material_4':  ('Dedinaru5c',        (2, 2)),
    'Material_5':  ('darkwood',          (4, 2)),
    'Material_6':  ('suburb_brick_2',    (2, 2)),
    'Material_7':  ('ceiling',           (3, 3)),
    'Material_8':  ('darkwood',          (2, 2)),    # the untextured one
    'Material_9':  ('cupboard',          (1, 1)),
    'Material_10': ('bluetilekitchen',   (2, 2)),
    'Material_12': ('crungewallpaper',   (2, 2)),
    'Material_15': ('container_lime_endnew', (1, 1)),
}
ROOM_DJ_SPARE_SKINS = ['darkwood', 'suburb_brick_1', 'GrassBrown', 'ceiling']

ROOM_DJ_TEXTURE_DETAIL = 0.5
# i measured the grass at 2.83 in the model's own units and the building
# rises 5.06 above it, so 0.62 puts the roof at about 3.1m - which reads as
# a house when your eyes are at 1.6m
ROOM_DJ_SCALE  = 0.62
ROOM_DJ_GRASS_Y = 2.83              # the whole thing drops by this so the

ROOM_DJ_GRID    = 0.8               # how coarse the lawn collider is, in
ROOM_DJ_AT     = Vec3(-800, 0, -800)

ROOM_DJ_SOLID_WALLS = True
ROOM_DJ_WALL_BUDGET = 10000
ROOM_DJ_VOID_COLOUR = RGB(0, 0, 0)  # everything outside the garden is black

# all four of these I stood on and printed in game, so they are WORLD
# positions rather than positions inside the room
ROOM_DJ_SPAWN_WORLD = Vec3(1058.69, -2.18, -591.37)
ROOM_DJ_EXIT_WORLD  = Vec3(1061.60, -2.18, -591.37)
ROOM_DJ_NPC_WORLD   = Vec3(1049.09, -2.18, -602.29)
ROOM_DJ_SET_WORLD   = Vec3(1050.23, -2.18, -600.09)

# the ground I actually stand on measured -2.18, not 0 - the model has its own
# idea of where its floor is and it is not where you would expect
ROOM_DJ_FLOOR_Y = -2.18
ROOM_DJ_HALF    = 14.0     # metres from the middle out to the invisible walls.
                           # Everything I placed is inside this.
ROOM_DJ_WALL_H  = 8.0      # how tall those walls are

ROOM_DJ_SPAWN  = Vec3(0.0, 0.4, 8.0)      # the old room-relative fallback,
ROOM_DJ_FACE   = 180
ROOM_DJ_EXIT   = Vec3(0.0, 0.0, 9.6)
ROOM_DJ_EXIT_YAW = 0
ROOM_DJ_DOOR_TEX = 'container_lime_endnew'

ROOM_DJ_SET_GLB   = 'dj_set'

ROOM_DJ_SET_SCALE = 0.075
ROOM_DJ_SET_LIFT  = 0.95
ROOM_DJ_SET_TEXTURE = 'store_control'
ROOM_DJ_SET_AT    = Vec3(0.0, 0.0, -1.2)
ROOM_DJ_SET_YAW   = 0

# THE DJ HIMSELF.
NPC_DJ_GLB    = 'psx_base_-_bearded_man'
NPC_DJ_HEIGHT = 1.75
NPC_DJ_AT     = Vec3(0.13, -2.18, -0.87)     # right at the decks
NPC_DJ_YAW    = 180
#the code that fits a model measures it and
# then drops it so its lowest point sits on the ground - but this model has a
# bit of geometry hanging below the feet, so "lowest point" was not his feet.
# This lifts him back up by hand until he is standing on the grass.
NPC_DJ_LIFT   = 0.35

# THE BEDFRAME UNDER THE DECKS.
DJ_BEDFRAME_ON    = True
DJ_BEDFRAME_OBJ   = 'bedframe'
DJ_BEDFRAME_AT    = Vec3(0.035, -2.00, -0.16)
DJ_BEDFRAME_LONG  = 2.07     # metres along X. I got this by standing at each
                             # end of where I wanted it and printing both
DJ_BEDFRAME_YAW   = 90
DJ_BEDFRAME_LIFT  = 0.02     # just off the floor so the two surfaces do not
                             # flicker against each other

# WHERE ALL THE INDOOR ROOMS LIVE. I park each one 150m from the last, far
# away from the village, and you get teleported into them. They are not
# really "inside" anything -
ROOM_BASE   = Vec3(600, 0, -600)
ROOM_SPACING = 150.0

# ROOM 0 - the horror corridor. Every number here was MEASURED by firing
# rays down through the model to find the real floor heights, not guessed.
# That is why you land on the top landing instead of inside it.
ROOM_CORRIDOR_GLB   = 'horror_corridor_vr_room_baked'
ROOM_CORRIDOR_SPAWN = Vec3(-3.7, 4.05, -9.0)

ROOM_CORRIDOR_FACE  = 80
ROOM_CORRIDOR_NPC   = Vec3(3.0, 0.02, -7.8)
ROOM_CORRIDOR_EXIT  = Vec3(-4.05, 3.90, -7.10)
ROOM_CORRIDOR_EXIT_YAW = 0
# the scientist. 70.16 units tall in the file, so this scale stands him eye to
# eye with me at 1.75m.
NPC_SCIENTIST_GLB   = 'half-life_scientist_einstein'
NPC_SCIENTIST_SCALE = 1.75 / 70.16

# ROOM 1 - the shop, where the organ seller is.
ROOM_SHOP_GLB     = 'abandoned__building__shop__old__house'
# I built my own counter inside an invisible box for this first, and it was
# awful. This is the original asset instead, untouched, just shrunk down.
ROOM_SHOP_SCALE   = 0.43
ROOM_SHOP_FLOOR   = 0.32       # in model units - the asset's own floor height
ROOM_SHOP_EXIT    = Vec3(9.83, 0.32, 0.085)
ROOM_SHOP_EXIT_YAW = None      # None = work it out automatically
ROOM_SHOP_EXIT_SIZE = (3.6, 4.7)   # model units, sized to fill the real gap
ROOM_SHOP_SPAWN   = Vec3(6.2, 0.32, 0.0)     # just inside that doorway
# and the world versions, printed in game, which win over the two above
ROOM_SHOP_SPAWN_WORLD = Vec3(752.53, 0.18, -601.24)
ROOM_SHOP_EXIT_WORLD  = Vec3(753.74, 0.14, -600.06)

# EVERYTHING OUTSIDE THE BUILDING IS THROWN AWAY. The asset is 48 x 48 metres
# of street, ground and background scenery, and I only want the shop. Dropping
# the rest at load time is far cheaper than hiding it.
ROOM_SHOP_DROP_MATERIALS = ('Ground', 'Environments')
ROOM_SHOP_KEEP_X = 11.0        # model units either side of the middle
ROOM_SHOP_KEEP_Z = 8.5
ROOM_SHOP_KEEP_Y = 10.0        # and nothing above the roof

# the textures in here are cheaper than the rest of the game on purpose -
# eight separate pictures stretched over one 33MB model, and it stuttered
# while they loaded in
ROOM_SHOP_TEXTURE_DETAIL = 0.25
ROOM_SHOP_FLOOR_DROP = 0.10    # a guaranteed floor just under the spawn, to
                               # catch me if the real one is missed
ROOM_EXIT_DOORS_SOLID = True   # the exit doors block you rather than being
                               # walk-through. E opens them.
ROOM_SHOP_FACE    = -90                      # looking into the shop at him
ROOM_SHOP_NPC     = Vec3(-6.6, 0.32, -1.0)   # behind the shelf at the back,
                                             # facing the door

SHOP_LOW_TEXTURES = True

SHOP_MATERIAL_SKINS = {
    'Wall':         ('ribcage',              (2, 3)),
    'Roof':         ('guts',                 (3, 2)),
    'Wood':         ('red neck together',    (1, 3)),
    'Irons':        ('Enemy_MegafuckElite2', (2, 2)),
    'Tiles':        ('randomrainbow',        (4, 1)),
    'glass':        ('Enemy_Security2',      (1, 1)),
    'Ground':       ('nerves',               (5, 5)),
    'Environments': ('Enemy_Orange',         (3, 2)),
}
# anything in the file that is not named above cycles through these instead,
# so a material I never mapped still gets SOMETHING rather than coming out
# white. That is how I found most of the missing ones - white walls, and also with the feature of everything showing up in the code output which is missing
SHOP_SPARE_SKINS = ['humanSUpremacy', 'memeface',
                    'grandma', 'grandma2', 'grandma3', 'crungewallpaper',
                    'funko', 'eye 1', 'eye 2', 'greenieface', 'black_hands 2',
                    'menunaked', 'red_marble', 'purple_carpet']

# this model started life as a Blender 5.0 file, and nothing outside Blender 5
# can open that format at all - so the game looks for an exported version by
# name instead of the .blend itself.
NPC_HANDSATWAIST     = 'handsatwaist'
NPC_TARGET_HEIGHT    = 1.75    # every NPC is scaled to this, so they all
                               # stand eye to eye with me whatever units their
                               # model came in

# THE TALKING CAMERA. When you press E on somebody the view swings round to
# show both of you, like Fallout New Vegas does it that waskind of my inspiration since its one of my favouite rpg games,
# instead of just freezing your head in place and putting a box at the bottom. This is my favourite bit.
DIALOGUE_CAM_ON = True         #the old way, just the text box

DIALOGUE_CAM_DISTANCE = 1.75   # metres out from them. Smaller is tighter.
DIALOGUE_CAM_LOOK_AT  = 0.80   # how far up their body to look, 0 = feet and
                               # 1 = top of the head.

DIALOGUE_CAM_LIFT     = 0.10

DIALOGUE_CAM_SIDE     = 0.0    # 0 = straight on.
DIALOGUE_CAM_FOV      = 55     # gameplay is 95. Narrower flattens the face;
                               # at 95 everyone looked fish-eyed up close
DIALOGUE_CAM_MOVE_TIME = 0.45  # seconds to glide in, and the same back out
DIALOGUE_CAM_TURN_NPC = True   # they turn to face the camera when you start

# THE CAMERA GOT ME STUCK MORE THAN ONCE, so these three are the safety net.
GAMEPLAY_FOV = 95
DIALOGUE_RESET_AFTER = 0.6


DIALOGUE_CAM_COOLDOWN = 0.25   # seconds after the glide home before E works
                               # again, so hammering E does not start the next
                               # conversation mid-glide

# THE VILLAGERS. The whole point was people walking around like they live there, rather than statues standing in the street.
VILLAGERS_ON = True

# WHERE THEY ARE ALLOWED TO WALK. The village gets covered in a grid of
# squares, and the ones that are not inside a wall become the map they use to
# find their way around. This is built once at startup.
VILLAGER_CELL       = 2.0
VILLAGER_CLEARANCE  = 1.1    # how far a square has to be from any wall to
                             # count. Without this they scrape along the sides
                             # of houses instead of walking past them
VILLAGER_MAX_SLOPE  = 0.55   # how much the ground may rise between two
                             # neighbouring squares. Steeper than this is a
                             # bank, not a path, and they should not climb it
VILLAGER_EDGE_MARGIN = 3.0   # stay this far inside the village edge, so
                             # nobody ever wanders off the end of the world


# HOW THEY MOVE!!!!
VILLAGER_SPEED      = 1.25   # metres a second. A walk, not a march.
VILLAGER_TURN_SPEED = 6.0    # how quickly they swing round to face the way
                             # they are going
VILLAGER_ARRIVE     = 0.55   # metres from a waypoint before it counts as
                             # reached
VILLAGER_IDLE_MIN   = 3.0    # seconds of standing still when they arrive
VILLAGER_IDLE_MAX   = 11.0   # "sometimes standing in one place"
VILLAGER_DOOR_CHANCE = 0.45  # how often their next destination is somebody's
                             # front door rather than just anywhere.
VILLAGER_DOOR_STAND = 0.9    # metres short of the door they stop, so they
                             # stand AT it instead of inside the wall
VILLAGER_REPATH_SECONDS = 6.0

#Each one runs a route,
# a walk step, a ground height lookup and four limb rotations. So i update the far ones less often, which you cant see anyway.
VILLAGER_LOD_ON   = True
VILLAGER_LOD_NEAR = 26.0    # metres. Just past the draw distance of 31, so
                            # anyone being throttled is barely visible anyway
VILLAGER_LOD_STEP = 0.25    # seconds between updates when they are far off

VILLAGER_LOD_NEAR_SQ = VILLAGER_LOD_NEAR * VILLAGER_LOD_NEAR

VILLAGER_LOD_RECHECK = 0.20   # seconds
# their thinking is spread out too, so all 39 never pick a new route on the
# same frame - that lands as one visible stutter instead of nothing
VILLAGER_THINK_SPREAD = 1.4

# HOW THEY WALK. All these numbers came from watching them and adjusting, not
# from anything clever.
VILLAGER_WALK_ANIM   = True
VILLAGER_LEG_SWING   = 26.0   # degrees the legs swing forward and back
VILLAGER_ARM_SWING   = 18.0   # degrees the arms swing. Deliberately less than
                              # the legs - equal amounts looks like marching
VILLAGER_STRIDE      = 1.35   # metres per full stride. Smaller = faster steps
VILLAGER_SWING_EASE  = 7.0    # how quickly the limbs settle back to standing
                              # when they stop, and lift again when they start
VILLAGER_BOB         = 0.0    # up and down of the whole body. Zero because I
                              # did not want them bobbing - a tiny amount like
                              # 0.02 does look good, so it is left here


#!!!!!!!!!!!!!
# CUTTING THE MODELS INTO LIMBS. I USED HEAVILY AI FOR THIS RIGGING BECAUSE I COULDN'T FIGURE IT OUT IN BLENDER AT THE TIME
# UNFORTUNATELY I KNOW HOW TO RIG AND MAKE AN ANIMATION NOW, but with ursina and python its really a hassle to do!
#!!!!!!!!!!!!!


# None of these models have a skeleton, so they cannot be animated normally.
# Instead each one is sliced into head, body, arms and legs by looking at
# where each triangle sits, and the pieces are hung off joints that rotate.
# These are the cut lines, measured off each model rather than guessed.
VILLAGER_RIGS = {
    # willong_ps1_horror_style / villagerMODEL.obj
    # feet y=-0.91, head top y=0.85, so 1.76 tall in its own units.
    'villagerMODEL': dict(
        hip_y=-0.30,        # legs are everything below this
        head_y=0.55,        # head is everything above this
        arm_x=0.20,         # arms are out past this, left and right
        shoulder_y=0.46,    # where an arm swings FROM
        leg_split_x=-0.02,  # the gap between the two legs is not at x=0
        hand_y=-0.10,       # lowest point of the arms, for reference
    ),

    'villagerMODEL2': dict(
        hip_y=0.62,

        head_y=1.52,
        arm_x=0.15,
        shoulder_y=1.46,
        leg_split_x=0.0,
        hand_y=0.80,
    ),
}

# NO TWO VILLAGERS WEAR THE SAME THING

# There are 40 here for 39 villagers, so it never repeats.
VILLAGER_BODY_TEXTURES = [
    'suburb_brick_1', 'suburb_brick_2', 'darkwood', 'red_marble',
    'crungewallpaper', 'ribcage', 'nerves', 'guts', 'randomrainbow',
    'humanSUpremacy', 'laterent', 'progresstexture', 'cover_edit_heavy',
    'grandma', 'grandma2', 'grandma3', 'funko', 'greenieface',
    'perfectbody', 'lifecourse', 'house100', 'monthlysubscription',
    'watchtimeMEME', 'memeface',
    'Enemy_MegafuckElite2', 'Enemy_Security2', 'Enemy_Orange',
    'eye 1', 'eye 2', 'greeter_face', 'menuhuman', 'menunaked', 'menugreen', 'bluetilekitchen',
    'Crumbfloor',
]
# THE HEAD KEEPS ITS OWN FACE. Only the body gets a random texture - giving
# the head one too turned everybody into a walking wallpaper sample and you
# could not tell they were people any more. These came out of the .glb files
# themselves; the tutorial that i used has the snippet I used to pull them.
VILLAGER_HEAD_TEXTURES = {
    'villagerMODEL':  'villagerA_tex_0',
    'villagerMODEL2': 'villagerB_tex_0',
}
# and the clothes the model came with, for the ones that keep their own
VILLAGER_OWN_BODY_TEXTURES = {
    'villagerMODEL':  'villagerA_tex_0',
    'villagerMODEL2': 'villagerB_tex_1',
}

# SMALL PEOPLE AND TALL PEOPLE. Every villager is scaled to one of these,
VILLAGER_HEIGHTS = [
    1.15,   # a child
    1.28,   # a child
    1.52,   # short
    1.60,
    1.68,
    1.75,   # the ordinary one, same as NPC_TARGET_HEIGHT
    1.75,
    1.82,
    1.90,   # tall
    2.02,   # very tall
]
VILLAGER_KEEP_OWN_CHANCE = 0.30   # roughly a third keep their original clothes
# only one model though
VILLAGER_MODEL_POOL = ['villagerMODEL']

VILLAGER_MODEL_YAW = {
    'villagerMODEL':  0,
    'villagerMODEL2': 0,      # assumed. Make it 180 if he walks backwards.
}

# TWO OF MY RECORDINGS ARE TIED TO SPECIFIC TEXT, because the words on screen
# and the words in the audio are the same take. These two always go together;
# the rest are handed out at random.
NPC_SCRIPTED_VOICES = {
    # the Spotify one
    'npc_realhuman2': [
        "I love this beat, I wonder if this is on Spotify premium, that is "
        "the stank, I am no larper, just enjoying the status quo, also "
        "human lol",
    ],
    # the longer one
    'npc_realhuman1': [
        "I am a real human, I have been put back together just like any "
        "other human. Can't you see? Anyway, how is the weather, when the "
        "beat drops I'm going to get a Netflix subscriptionship with ads "
        "and watch the best 500 shows that no one actually knows. I love "
        "Captitalism!",
    ],
}

# these five go to random villagers, a different five every launch - but all
# five are ALWAYS used, because they are dealt out like cards rather than
# picked one at a time. Picking at random means some never come up.
NPC_ROTATING_VOICES = [
    'npc1viimane',
    'npc2VEELUKS',
    'npc3JO',
    'npc3HEY',
    'npcline1',        # "Npc line 1.m4a.mp4", converted to .wav cuz apple blabla imported wrong
]

# every recorded clip in one list, so the code that shuts all the voices up  can find them without me remembering to add each new one in two places
ALL_NPC_LINE_CLIPS = list(NPC_SCRIPTED_VOICES.keys()) + list(NPC_ROTATING_VOICES)

# EVERYTHING THE VILLAGERS SAY
# some of these are atrocious, this is my capitalism bad part of the game, not worth reading through all fo them its a lot.
VILLAGE_SPEECHES = [
    # 1
    ["All our systems have been down today because of a logic bomb "
     "activated by a former developer. I'm not supposed to say this but "
     "I'm glad it happened.",
     "Just to clarify I'm only here until I can my own company off the "
     "ground. I'm trying to break into potato farming logistics."],
    # 2
    ["You seem different from the other security guys. Like you have less "
     "emotion somehow. Haha just messing with you bro.",
     "They're saying Pycharm and Github doesn't run on my PC because of "
     "the Mac book pro im using. I'm not having that, I'm leaving a "
     "negative review. Also this game is just a cruelty squad copy, "
     "CANCELLED!"],
    # 3
    ["I am fine. I shine. I am simply divine...",
     "I am head of the HR Department around here. I am feared and loved.",
     "Human resources... Simple material to be formed as I please, into my "
     "own image. That's how it goes around here.",
     "My dream, a large ball of human bodies rolling across vast plains, "
     "flattening everything it comes across.",
     "Ahhh.... I would love that."],
    # 4
    ["hEY i AM dANIEL mULLINS! One more year and I'm going to have enough "
     "money to retire for good.",
     "This resort business just isn't for me. Complaining customers and "
     "know it alls who think they know how to run this place better than "
     "me.",
     "I will NOT add a water slide. Where would it even go?",
     "Sigh... I should have thicker skin by now.",
     "Thanks for listening. I feel so much better. I never get to say "
     "these things to anyone."],
    # 5
    ["I'm the most powerful person in this room. I control this situation. "
     "Everyone's dancing to my tune...",
     "NrNrNr BNBNBNBNBNBNBNRONICHITY.... NNNNNNTRONNNNNNCHTONOMONOTRACHIA..... "
     "CRNNNNNNTRRRRRRHYRAXIAPLASTIA....",
     "Theory time. Us civilians are a writhing mass of flesh, vaguely "
     "connected by a vegetative psychological link. Our value is determined "
     "by an extradimensional being who is toying with us. We have no "
     "capacity for thought, we're simply an ecosystem of flesh.",
     "You're so composed and cool. Are you an artist?"],
    # 6
    ["I need to come here and really let go so I can work on my creative "
     "investment portfolio. I have an artistic take on finance.",
     "You invest in the stock market? I'm impressed.",
     "Where'd you get that sexy outfit?",
     "Hearbeat... Good. Brainwaves... Perfect. Blood pressure... "
     "Astronomical.",
     "Power is flowing through me. I'm a beast. I'm a destroyer. Get in my "
     "way and I will kill you."],
    # 7
    ["I feeel like everyone has big personalities these days, I enjoy "
     "fishing, I live in the Crumbbrooks, Sometimes I like going to epic "
     "club complexes, Fast cars.... Luxury vodka... Gaming BIOPOD. You name "
     "it. I probably tried it, but thats not for me... I'm more of a Tech "
     "Basics guy myself, \"Game syndrome\" have you heard of it, it's when "
     "you can't finish a game and you keep adding random npc lines. Anyway "
     "thanks for listening, you are a really good listener"],
    # 8
    ["I get intense gratification from bullying losers online.",
     "You won't last five seconds around here.",
     "I could snap you like a twig. I have a home gym.",
     "Pathetic...",
     "To kill is to live. I live a warrior lifestyle.",
     "Eat raw eggs. Sperm. Datura. And you can achieve what I have full "
     "natty. If you have what it takes.",
     "Greatness is achieved through violence of action."],
    # 9
    ["I'm the village's carpenter.",
     "I'm not like the others. I don't care where you're from. Business is "
     "business.",
     "They detest me but none of them can work with wood at all. They tried "
     "and one of their houses ended up collapsing. They need me.",
     "Still. I'd stay away from the village. You never know what those "
     "people will come up with next.",
     "The air around here can cause severe psychological damage."],
    # 10
    ["My traditional biotech remedies won't work on an augoid like you.",
     "There's no saving you. I think you should be purified.",
     "I have received the blessings of the Triagon."],
    # 11 (the first of my two 11s)
    ["Bataille claims that \u201cmadness itself gives a rarified idea of the "
     "free \u2018subject\u2019 unsubordinated to the [socially constructed] "
     "\u2018real\u2019 order and occupied only with the present\u201d "
     "(1988a, p. 58). Don't ask me how I remembered that reference, I study "
     "Digital Media."],
    # 11 (the second)
    ["The bright contrasting colors and wonton texturing of the world "
     "decodes the features of capitalist space, which are then recoded "
     "through gameplay as the player comes to parse the space not through "
     "access to points of exchange, but as a smooth space which the player "
     "is liberated to cut across towards their own ends. Truly... a weird "
     "game i don't even get the story."],
    # 12
    ["I remembered first, the pearly gates, reaching out to grab me, but im "
     "talking to you before that The pictures came, remembering with it. - "
     "telling me what to see Somebody painting behind my eyes, where do I "
     "belong? I need something more A painter in my mind A turn of the "
     "decade A tourist in a dream. A visitor on my own name. A "
     "half-forgotten song Where do I belong?",
     "Tell me what you see. I need something more."],
    # 13
    ["You've given me too much to feel,\nYou've almost convinced me I'm "
     "real.",
     "I don't remember any of the trips/vacations/or get aways.",
     "I remember the smell of a car window that wasn't ours, parked in a "
     "town that spoke a different way to us.",
     "It was never the moments we planned. It was the ones we never knew "
     "were important.",
     "Find it, Find it in the bathtub spider you saved. In the postman's "
     "worn shorts and sleeves and the ever-happy whistle. In birds singing "
     "in the morn, before you've even touched the cold side of your "
     "pillow."],
    # 14
    ["You've been here before. I'm sure of that.",
     "Nobody knows where the glow in the horizon comes from. This is not a "
     "place of knowledge.",
     "Pain.",
     "You're going to the Doom level right? Why?",
     "You can kill me but it won't end this.",
     "You're not from around here. I can tell.",
     "There's an infinite amount of planes. They all contain the same "
     "amount of suffering."],
    # 15
    ["I'm the Chief Finances Officer. But I also handle other types of "
     "\"asset liquidations\"",
     "Oh you work for me, Gray Matter?",
     "Since you're here... Could you deal with the others for me? I hate "
     "this work environment. It needs a hard reset.",
     "Oh you're here to do that? That's great!",
     "Get to it then alright you can kill everyone anyway."],
    # 16
    ["Second Target",
     "I'm about to master the swamp. Becoming swampform.",
     "Soon it'll be over for all of you. My pores are big and they ooze "
     "with power.",
     "Witness my rebirth. In a week or so.",
     "It's going to be breathtaking."],
    # MY SECOND BATCH
    # 18
    ["The prizes aren't so good. Definitely not worth it. Yet here I am.",
     "I'm financially successful. I'm desirable. I'm a multi-millionaire"],
    # 19
    ["...Sorry what did you say? I was thinking about controlled "
     "depopulation. There's too many of us on this planet."],
    # 20
    ["I love deconstrcuted classic rock. Huh you don't know about it? You "
     "don't listen to music? Freak!",
     "Please go to changing room and get dressed."],
    # 21
    ["Stuck in a rut? The good people at Pure Optics will fix you right "
     "back up.",
     "I can't remember the name oof the dude but I'm sure you can find it.",
     "Good luck, I can see that you have what it takes to become a top "
     "exec."],
    # 22
    ["(Hahaha... He can't see me.)",
     "(...)",
     "Wait, you know I'm here? How's that even possible?",
     "The smell? God, should have known. I paid good money for this "
     "invisibility cloack but it's completely useless. Just like me.",
     "Despite having money I will never amount to anything. This is what "
     "it's like to be the child of a trillionaire. Ridiculous. Pathetic."],
    # 23
    ["im 50, my child has serebeal palpsy, i hate my job, my friend is a "
     "trillionaire, I think im gonna start cooking meth, but make it 99% "
     "pure and then become a drug lord, maybe call myself Heisenberg"],
    # 24
    ["Theres this guy Ulas, weirdo, apparently he lives on "
     "S\u00fcsen Heide 12, L\u00fcneburg, lower saxony. I also think he "
     "already took tech basics, what a nerd."],
    # 25
    ["Have you heard of \"Flower in a Stonefield\" the coolest band around, "
     "I'm sure you get ads of their new single \"Gasoline\" all the time. "
     "they rule!"],
    # 26
    ["I hate Flower in a Stonefield, that band sucks"],
    # 27
    ["I really like the singer of flower in a stonefield, but the guitarist "
     "is weird, im not racist or anything, but I think he is from Estonia, "
     "weirdos over there. All they do is go to the sauna and cold lakes, "
     "theyr beer is the worst."],
    # 28
    ["SOOAOUFAOUFNAODMAOIMOAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"],
    # 29
    ["what are you... aISHFOUAHDOAJOIAJFOUANFOUNOUN"],
]
VILLAGERS = [
    # THE FIVE RICHEST
    # rich=True keeps the texture that came out of their own .glb. In a
    # street where everybody else is wearing brick and offal, the people who
    # look like they were MEANT to look that way read as the wealthy ones.
    dict(name='A NEIGHBOUR', rich=True),
    dict(name='A NEIGHBOUR', rich=True),
    dict(name='A NEIGHBOUR', rich=True),
    dict(name='A NEIGHBOUR', rich=True),
    dict(name='A NEIGHBOUR', rich=True),

    # THE TWO WITH RECORDINGS OF THEIR OWN
    # Fixed voice AND fixed words, because the words and the audio are the
    # same performance - so nothing about these two gets randomised.
    dict(name='A NEIGHBOUR', voice='npc_realhuman2',
         lines=NPC_SCRIPTED_VOICES['npc_realhuman2']),
    dict(name='A NEIGHBOUR', voice='npc_realhuman1',
         lines=NPC_SCRIPTED_VOICES['npc_realhuman1']),

    # AND AAAAAALLLLL THE REST OF THE VILLAGERS
    # NO model, NO height, NO lines - all three get chosen for them:
    #model   at random from VILLAGER_RIGS, seeded off their index
    #height  at random from VILLAGER_HEIGHTS - children to very tall
    #lines   dealt from VILLAGE_SPEECHES, one each while they last
    # 29 of them are name-only like this. 37 villagers have no lines of
    # their own, and i have written 29 speeches, so 30 get a speech to themselves and the last 7 share. See
    # hand_out_speeches() - it reshuffles for the leftovers so the repeats
    # are spread around instead of landing on the end of the list.
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),

#this is just goofing around, with height here
    dict(name='A NEIGHBOUR', height=3.40),   # comically big
    dict(name='A NEIGHBOUR', height=2.90),   # comically big
    dict(name='A NEIGHBOUR', height=0.90),   # comically small
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'), dict(name='A NEIGHBOUR'),
    dict(name='A NEIGHBOUR'),
]
# 39 IN TOTAL: 5 rich, 2 with my own recordings, 32 ordinary - three of
# those absurdly sized because i thought it was funny.


NPC_MODEL_PITCH = {
    'veritytm': -90,          # the old DJ, authored Z-up

    'psx_base_-_bearded_man': 0,
}

NPC_MODEL_YAW = {
    'default': 180,
    'veritytm': 180,          # the old DJ

    'psx_base_-_bearded_man': 90,

    'half-life_scientist_einstein': 180, #ccorrect facings
    'handsatwaist': 180,
    'male_01_citizen': 180,
    'villagerMODEL': 180,
    'villagerMODEL2': 180,
}


#WEAPOOOOOOOOOOOOOOOOOOOOOOOONS
WEAPON_FOLDER  = 'weapons'
WEAPON_TEXTURE = 'level'

# order matters: this is the order i cycle through with the mouse wheel, and
# 'unlocked_at' is the level index where the pickup starts appearing.
WEAPONS = [ #this is tha basic way of putting a entity into the game in ursina, im just adding texture colour and some gun sepcific modifications.
    dict(key='pistol',  name='9MM',              model='pistol_9mm', glb=True,
         damage=0.7,  cooldown=0.40, pellets=1, spread=0.000, sound='pistol',
         kick=6,  unlocked_at=0, start_with=True,
         pos=Vec3(0.19, -0.16, 0.50), rot=Vec3(0, 92, 0), scale=0.180),

    dict(key='shotgun', name='SHOTGUN',         model='shotgun',
         damage=1.1,  cooldown=1.3333, pellets=7, spread=0.100, sound='shotgun',
         kick=20, unlocked_at=1, start_with=True,
         pos=Vec3(0.19, -0.17, 0.60), rot=Vec3(0, 0, 0), scale=0.172),

    dict(key='rifle',   name='RIFLE',           model='rifle',
         damage=0.6,  cooldown=0.14, pellets=1, spread=0.01, sound='rifle',
         kick=5,  unlocked_at=2, start_with=False,
         pos=Vec3(0.19, -0.16, 0.75), rot=Vec3(0, 0, -0.05), scale=0.155),


    dict(key='watergun', name='WATER GUN',      model='lowpoly_watergun',
         glb=True,
         # 1.5x STRONGER. 0.3 -> 0.45. It is still weaker
         # than the rifle (0.6) it was cloned from, which keeps the joke
         # it is a water pistol - but it no longer takes twice the magazine.
         damage=0.45, cooldown=0.14, pellets=1, spread=0.01, sound='rifle',
         kick=5,  unlocked_at=0, start_with=False,
         pos=Vec3(0.19, -0.16, 0.75), rot=Vec3(0, 0, -0.05),
         scale=0.00114,                       # was 0.00205, /1.8
         pickup_scale=0.0008,                 # about key-sized
         pickup_at=Vec3(25.56, -2.23, 23.84)),  # yours

# this is so fun i can just make my guns overpowered
    dict(key='minigun', name='MINIGUN',         model='minigun',
         damage=0.55, cooldown=0.0467, pellets=1, spread=0.022, sound='minigun',
         kick=3,  unlocked_at=3, start_with=False, spin_barrel=True,
         pos=Vec3(0.23, -0.1, 0.60), rot=Vec3(0, 0, -0.05), scale=0.100),

    dict(key='rocket',  name='ROCKET LAUNCHER', model='rocket-launcher',
         damage=14.0, cooldown=1.5, pellets=1, spread=0.0, sound='rocket_launcher',
         kick=20, unlocked_at=3, start_with=False, rocket=True,
         pos=Vec3(0.20, -0.10, 0.68), rot=Vec3(0, 0, 0), scale=0.150),

    dict(key='angler',  name='HEAVY ANGLER',     model='heavy_angler', glb=True,
         damage=15.0,  cooldown=0.16, pellets=2, spread=0.001, sound='rifle',
         kick=9,  unlocked_at=99, start_with=False,
         pos=Vec3(0.17, -0.13, 0.44), rot=Vec3(0, 90, 0), scale=0.00175),
]

PLAYER_DAMAGE_MULT = 2.4

WEAPON_RANGE   = 200
ROCKET_SPLASH  = 10.0        # how far a rocket's blast reaches

# the guns lying on the floor waiting to be picked up
PICKUP_SCALE   = 0.10
PICKUP_SPIN    = 55         # degrees per second, so they turn on the spot
PICKUP_RADIUS  = 2.4        # how close you have to get

# THE REAL E1M1 EXIT CANNOT BE REACHED. I build my own
# exit door at the far end instead and texture it to match.
KEY_TEXTURE      = 'artworks-2pm5zExCuJ8SeYcQ-4RWtIQ-t500x500'   # red, stands
                                                                 # in for a keycard
EXIT_TEXTURE     = 'store_control'
EXIT_SIGN        = 'store_freedom'

# THE HEALTH PICKUP IS A LIVER, which fits the game better than a medkit would anyway.

HEALTH_ON        = True
HEALTH_TEXTURE   = 'guts'
HEALTH_FALLBACKS = ['nerves', 'ribcage', 'red_marble']
HEALTH_LABEL     = 'LIVER'
HEALTH_AMOUNT    = 200          # health restored, out of PLAYER_MAX_HP
HEALTH_PER_LEVEL = 9           # how many are scattered around a level
HEALTH_MIN_GAP   = 14.0        # metres apart, so they are not all in a heap
HEALTH_RANGE     = 2.0         # how close you have to get to pick one up
HEALTH_SIZE      = (0.45, 0.30, 0.45)
HEALTH_MIN_FROM_SPAWN = 6.0    # never right on top of you when you arrive

KEY_PICKUP_RANGE = 2.2
EXIT_RANGE       = 3.0

NAV_GRID_STEP    = 2.0

# WHERE THE EXIT DOORS GO. Every one of these is somewhere I actually stood
# and printed.
EXIT_SPOTS = [
    Vec3(75.14, -1.00, -30.25),
    Vec3(16.85, -0.08, 42.95),     # this is the one that was in the ceiling
    Vec3(75.17, -1.00, -45.45),    # and this one was inside a wall
]

# which way each one faces. Level 2's needed turning 90 degrees - and because
# the survive level reuses level 2's door, fixing one fixed both.
EXIT_SPOT_YAW = [
    0,      # level 1, and level 4 reuses it
    90,     # level 2, and the survive level
    0,      # level 3
]
EXIT_BIG_YAW = 0     # the wall-sized door has its own, since it is not in
                     # the list above

BOSS_SPAWN = Vec3(41.45, -1.00, 5.43)
BOSS_CROWD = 8               # extra enemies posted around him
BOSS_CROWD_RADIUS = 26.0     # how far around him they spread out

EXIT_BIG_ON = False
EXIT_BIG_SPOT = Vec3(69.83, -1.61, -8.53)
EXIT_BIG_SIZE = (7.0, 5.0, 0.35)               # width, height, thickness

EXIT_DOOR_DROP = True

KEY_SPOTS = [
    Vec3(41.45, -1.00, 5.43),      # level 2's key
    Vec3(52.67, -0.08, 55.37),
    Vec3(28.28, -3.15, 13.74),
]
# level 1 gets the easiest key to find
KEY_SPOT_FIRST = Vec3(8.34, -0.69, 14.90)

ENEMY_ZONE_RADIUS = 30.0
ENEMY_MAX_HEIGHT = 12.0

# TWO PLACES IN THE NORTH-EAST NOTHING SHOULD BE ABLE TO REACH an insanely annoying bug , and enemies
# kept spawning in them anyway. I found them by hearing shooting from
# somewhere I could not get to. Blocked off by coordinates.
DOOM_DEAD_ZONES = [
    (Vec3(88.79, 4.42, 21.40), 11.0),
    (Vec3(90.84, -0.74, -4.17), 11.0),
]
DOOM_SEAL_DEAD_ZONES = True    # and put a solid box over them as well, so
                               # nothing can wander in either


def in_dead_zone(p):
    for centre, r in DOOM_DEAD_ZONES:
        if (p.x - centre.x) ** 2 + (p.z - centre.z) ** 2 < r * r:
            return True
    return False
# How far apart the dedicated spawn points are. Bigger = fewer, more
# recognisable places they come from; smaller = more scattered.
ENEMY_SPAWN_SPACING = 3.0

# A thin strip at the top with a marker that slides as you turn, the way
# most open world games do it. I kept it deliberately plain so it does not
# pull your eye away from the game.
COMPASS_WIDTH   = 0.32
COMPASS_Y       = 0.455
COMPASS_FOV     = 80        # degrees either side before the marker pins to the edge

# an idea I tried and turned off: keep the whole level asleep until you pick
# up the key. It made the first half boring, so now they wake normally.
ENEMY_HOLD_UNTIL_KEY = False
ENEMY_WAKE_DISTANCE  = 20.0
ENEMY_WAKE_MESSAGE   = 'they know you are here now' #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# WHERE THE ENEMIES STAND. I never typed the rooms in anywhere - the game
# MEASURES them at startup by firing rays out from every walkable spot and
# seeing how much open space is around it. Wide open space is a room, narrow
# space is a corridor, and they get filled differently. This was much easier
# than placing 40 enemies by hand in a map i did not draw.
ENEMY_PER_ROOM       = 4      # four in every room
ENEMY_IN_CORRIDORS   = 6      # and some out in the corridors too
ENEMY_ROOM_WIDTH     = 5.5    # metres across before a space counts as a room
ENEMY_ROOM_PROBE     = 16.0   # how far those rays bother looking
ENEMY_ROOM_MIN_SPOTS = 4      # a patch smaller than this is not a room
ENEMY_ROOM_MAX       = 9      # keep at most this many rooms, biggest first
ENEMY_POST_SPACING   = 3.0    # metres between two of them in the same room

# THE ROOM YOU ARRIVE IN HAS TO BE EMPTY. Spawning into a fight before you
# have even turned around is just unfair, so i place nothing within this
# distance of where you start.
ENEMY_POST_MIN_FROM_SPAWN = 22.0
# and they stay asleep until you have walked this far, whatever they can
# see. Slightly less than the distance above, so the first one you meet
# wakes up as you approach rather than the instant you move.
ENEMY_QUIET_RADIUS = 18.0
ENEMY_ROOM_STEP_Y    = 2.6    # a floor this much higher than another is a
                              # different storey, not the same room

# ONCE AWAKE THEY ARE ALWAYS COMING FOR YOU. There is no target picking, no
# searching and no losing interest - these numbers only decide the moment it
# starts. Anything cleverer than that just read as them being confused.
ENEMY_SIGHT        = 70.0     # metres they can see you, with a clear line
ENEMY_SIGHT_ARC    = 360      # degrees of vision. Real DOOM uses 180 - a
                              # monster cannot see behind itself - but I want
                              # them to find you, so this is all the way round
ENEMY_HEARING      = 22.0     # this close and they do not need to see you
ENEMY_SHOT_HEARD   = 45.0     # your gunshot wakes everything this near to you
ENEMY_ALERT_SPREAD = 16.0     # one waking wakes its neighbours, so a room
                              # comes alive together (DOOM's sound spreading)
ENEMY_REACTION     = (0.12, 0.45)   # seconds between spotting you and the
                                    # first shot. Without a pause they fire
                                    # the instant you round a corner, which
                                    # feels like being sniped, not seen
ENEMY_ANIM_DISTANCE = 55.0    # past this a sleeping enemy does not even
                              # animate. Free framerate, invisible in play
ENEMY_LOS_TICK     = 0.26     # how often each awake enemy fires one ray to
                              # check it can still see you. Was 0.18 - with
                              # thirty awake that is over a hundred rays a
                              # second, and it showed
ENEMY_FORGET       = 10.0     # seconds it keeps walking towards where it last
                              # saw you after losing sight

# THE FIREBALL SPEED IS DOOM'S OWN. A real imp fireball moves 10 map units
# per tic at 35 tics a second, which is 350 units a second - and nightmare
# mode doubles it to 700. I used the nightmare number because at 350 you can
# simply walk away from them.
ENEMY_PROJECTILE_SPEED = 700.0 * DOOM_SCALE      # works out about 27 m/s
ENEMY_PROJECTILE_HIT   = 1.05    # metres from your middle that counts as a hit
# a hard limit on how many shots can be in the air at once. Thirty enemies
# firing every second or so is a lot of objects each doing their own
# collision check every frame, and past about this many you feel it.
ENEMY_MAX_PROJECTILES  = 26
ENEMY_FRIENDLY_FIRE    = False   # True gives you DOOM infighting, where their
                                 # shots hit each other and they thin
                                 # themselves out. Fun, but it made fights
                                 # unpredictable in a way I did not want

# THEY AIM AT WHERE YOU WERE, not where you are. The aim gets taken the
# moment they fire and then the shot travels - so strafing actually works and
# standing still gets you hit. That one decision is most of what makes them
# feel fair, and it took me a long time to work out that this was the thing
# that was wrong rather than their damage or their speed.
ENEMY_AIM_LAST_POS = True
ENEMY_AIM_JITTER   = 0.30    # metres of slop, so twelve of them do not all
                             # put a shot through exactly the same pixel

ENEMY_AGGRO    = 250          # a hard cutoff, and nothing on this map is ever
                              # this far away - which is the point. They never
                              # stand around doing nothing.
ENEMY_MELEE    = 2.4          # they hit you inside this range
ENEMY_FIRE_MIN = 1.6          # closer than this and they swing instead of shoot
# an enemy that can already see you and is inside ENEMY_ADVANCE_RANGE plants
# its feet and shoots. Further out and it walks in first. Without this they
# all ran at you together and it turned into a pile-on.
ENEMY_STAND_AND_SHOOT = True
ENEMY_ADVANCE_RANGE   = 18.0

# HOW THEY WALK, which is DOOM's own method - pick a direction, try it, and
# if it does not work try a different one. No pathfinding at all.
ENEMY_DIR_RETHINK  = (0.5, 1.2)   # seconds before re-aiming their walk at you
ENEMY_TRY_WALK     = 0.95         # metres they test ahead before committing
ENEMY_DROP_MAX     = 2.5          # they will not step off anything higher
                                  # than this. DOOM has the same check, and it
                                  # is what keeps them out of the sludge and
                                  # off the ledges
ENEMY_SEPARATION   = 0.0          # 0 means they can overlap each other. Above
                                  # 0 they push apart, which looks better and
                                  # costs more

# EVERY ENEMY IS A SPRITE, not a 3D model - a flat picture that always turns
# to face you, with eight different images depending which side you are on.
# That is how the real DOOM did it and it is far cheaper than models.
ENEMY_TIERS = {
    # level 1 - weakest, but it does shoot. Slow, sparse, easy to dodge.
    'weak':    dict(sprite='PSPO', hp=2,  width=1.2, speed=4.4, damage=5,
                    ranged=True,  cadence=2.6, tint=RGB(255, 255, 255)),
    # the casual one. Shotgun, quick pairs of shots.
    'casual':  dict(sprite='SPOS', hp=5,  width=1.3, speed=4.8, damage=8,
                    ranged=True,  cadence=1.8, tint=RGB(245, 245, 255)),
    # stronger. Chaingun cyborg, fires often, holds its distance.
    'strong':  dict(sprite='CIM2', hp=11, width=1.5, speed=4.0, damage=11,
                    ranged=True,  cadence=1.1, tint=RGB(255, 235, 225)),
    # the mystery one. The ONLY pure melee tier - fast, silent, and it just
    # runs at you. You find out what it is by letting it reach you.
    'mystery': dict(sprite='HSPO', hp=8,  width=1.2, speed=4.6, damage=15,
                    ranged=False, cadence=0.9, tint=RGB(205, 205, 235)),
    # the secret one. Rare, tough, hits hard at range.
    'secret':  dict(sprite='SSGH', hp=17, width=1.4, speed=3.6, damage=18,
                    ranged=True,  cadence=1.4, tint=RGB(255, 215, 165)),
    # a second melee-ish type so the mix isn't all one silhouette
    'runner':  dict(sprite='TROO', hp=6,  width=1.2, speed=4.4, damage=10,
                    ranged=True,  cadence=1.6, tint=RGB(235, 245, 235)),
    # Hendrik. Three times the size of anything else, and he walks in from the
    # far side of the map rather than being announced.
    'boss':    dict(sprite='SKEL', hp=95, width=2.2, speed=3.4, damage=24,
                    ranged=True,  cadence=1.0, tint=RGB(255, 255, 255)),
}

# which kinds turn up on which level. This is unused now - the levels pick
# their own mix in the LEVELS table instead - but I am leaving it because it
# is a much easier place to read what each level is SUPPOSED to feel like.
ENEMY_ROSTER = {
    1: ('weak', 'runner', 'secret'),
    2: ('weak', 'casual', 'runner'),
    3: ('casual', 'strong', 'runner', 'mystery'),
    4: ('weak', 'strong', 'mystery', 'casual', 'runner', 'secret'),
    5: ('strong', 'mystery', 'secret', 'casual', 'weak', 'runner'),
}
SECRET_ENEMY_CHANCE = 34.0   # one in this many is the rare one, level 3 on

# THE NAME TAGS ARE OFF, and they were a real framerate problem rather than
# just an ugly one. Every floating name is a Text object, and in Ursina a Text
# is a whole mesh built out of letter shapes - sixty of those hanging in the
# air, all being redrawn and re-sorted every frame, was one of the worst
# things in the game. The names themselves are still here because I like them.
ENEMY_NAME_TAGS = False

ENEMY_NAMES = [
    'Larry Page', 'Lloyd Blankfein', 'Carly Fiorina', 'Mark Zuckerberg',
    'Elon Musk', 'Linda Yaccarino', 'Travis Kalanick', 'Adam Neumann',
    'Sam Bankman-Fried', 'Dave Calhoun', 'Kay Whitmore', 'Warren Anderson',
    'Lehman Brothers', 'Ken Lay', 'Gerald Ratner', 'John Sculley',
]
BOSS_NAME   = 'TECH BASICS'
NAME_SHOW_SECONDS = 100.0      # how long a tag stays up, if they are ever
NAME_SHOW_DISTANCE = 55.0      # switched back on, and how far you can read it
BOSS_SIZE_MULT = 2.5           # the boss stands two and a half times the
                               # height of anything else on the map

# ENEMIES WERE BEING FLUNG INTO THE AIR AND THIS NUMBER IS WHY!!! This one
# cost me an entire evening. Each one finds the floor by firing a ray down,
# and the ray has to start ABOVE the enemy or it starts below the floor and
# finds the next one down. But start it too high and it finds the top of
# whatever they are standing next to instead - so they would suddenly
# teleport onto a wall. It was 1.6; 0.95 is high enough to step up a DOOM
# stair and too low to catch a wall top.
ENEMY_STEP_UP = 0.95
# and how fast they fall when there is genuinely no floor under them. Without
# this they used to just hang in the air wherever the ray last found something.
ENEMY_FALL_SPEED = 14.0

# enemy speeds are a RATIO of how fast I walk, not a flat number - so if I
# ever change the player speed they all keep the same relationship to me.
# This caps how much faster than me anything is allowed to be.
ENEMY_SPEED_CAP = 1.40

# THE SLUDGE THAT HURTS YOU IS FOUND BY TEXTURE NAME, which i thought was a
# really clever thing about DOOM when i found out. A damaging floor is not
# marked as anything special in the map - it is just a floor wearing one of
# these textures, and the game knows what they mean. NUKAGE is the green,
# SLIME the brown, and LAVA and BLOOD do what they say.
TOXIC_TEXTURES = ('NUKAGE', 'NUKE', 'SLIME', 'LAVA', 'BLOOD', 'FWATER')

# there is exactly one group in the map with no picture to go with it, called
# 'Default' - geometry the exporter never assigned a material to. It gets this
# so it is not a white hole in the middle of a wall.
DEFAULT_TEXTURE = 'STARTAN3'

# THE DOORS IN THE MAP ARE FROZEN SHUT. The .obj is a snapshot of the level
# at one moment, so every door in it came in as a solid slab. These names are
# how i find them and make them work again. DOORTRAK and DOORSTOP are
# deliberately NOT in the list, because those are the frames the door slides
# in and not the door - i left them in once by accident and lifted the whole
# doorframe off the wall, which looked ridiculous.
DOOR_TEXTURES  = ('BIGDOOR', 'DOOR3', 'EXITDOOR')
DOOR_OPEN_RANGE = 3.0      # metres away before it starts to lift
DOOR_LIFT       = 2.2      # how far up it goes
DOOR_SPEED      = 3.0      # metres per second
DOOR_CLUSTER    = 4.5      # triangles closer together than this are treated
                           # as one door, so both halves lift together
TOXIC_DPS      = 15.0      # health a second while you stand in the sludge
TOXIC_TICK     = 0.1       # how often that is applied


# HOW DOOM NAMES ITS SPRITE FILES, which is the whole reason the enemies
# work, and it took me a while to get my head round. Every file is called
# NAMEFR: four letters for the monster, then a letter for the animation frame
# (A, B, C...), then a digit 1-8 for which side you are looking at it from.
# So SPOSA1 is "shotgun guy, first frame, seen from the front". Some files
# have EIGHT characters - SPOSA2A8 - which means one image covers two
# opposite angles and the second one is mirrored.
SPRITE_DIR   = 'sprites'
SPRITE_PX    = 56.0        # a DOOM player is 56 map units tall, so this is
                           # the yardstick everything else is measured against
_sprite_index = {}         # 'SPOS' -> {'A': {1: ('SPOSA1', False), 2: (...)}}
_sprite_folder = None      # filled in by build_sprite_index()


def build_sprite_index():
    global _sprite_folder
    # indexed folder lookup, not a fresh walk of the project - see find_folder()
    _sprite_folder = find_folder(SPRITE_DIR)
    if _sprite_folder is None:
        print('!! no sprites/ folder found - enemies will fall back to quads')
        return _sprite_index
    for f in _sprite_folder.iterdir():
        if f.suffix.lower() != '.png':
            continue
        stem = f.stem
        if len(stem) < 6 or not stem[5].isdigit():
            continue
        prefix, frame, angle = stem[:4], stem[4], int(stem[5])
        table = _sprite_index.setdefault(prefix, {})
        table.setdefault(frame, {})[angle] = (stem, False)
        # the mirrored half of a packed pair: SPOSA2A8 -> also angle 8, flipped
        if len(stem) == 8 and stem[7].isdigit():
            table.setdefault(stem[6], {})[int(stem[7])] = (stem, True)
    return _sprite_index


def sprite_frame(prefix, frame, angle):
    table = _sprite_index.get(prefix, {}).get(frame)
    if not table:
        return None, False
    for key in (angle, 0, 1):
        if key in table:
            return table[key]
    return next(iter(table.values()))


def sprite_frames_present(prefix, letters):
    have = _sprite_index.get(prefix, {})
    return [c for c in letters if c in have] or ['A']


def sprite_pixel_height(prefix):
    stem, _ = sprite_frame(prefix, 'A', 1)
    if not stem or _sprite_folder is None:
        return SPRITE_PX
    try:
        from PIL import Image
        with Image.open(_sprite_folder / f'{stem}.png') as im:
            return float(im.size[1])
    except Exception:
        # Pillow missing is not a reason to crash - assume player height
        return SPRITE_PX


def sprite_texture(stem):
    if stem in _sprite_tex:
        return _sprite_tex[stem]
    tex = None
    if _sprite_folder is not None:
        path = _sprite_folder / f'{stem}.png'
        if path.exists():
            try:
                tex = load_texture_scaled(path)      # potato mode
                tex.filtering = None       # crisp pixels, not smeared mush
            except Exception as exc:
                print(f'!! sprite {stem} failed to load: {exc}')
        else:
            print(f'!! sprite file missing: {path}')
    _sprite_tex[stem] = tex
    return tex


_sprite_tex = {}

# THE CONFRONTATION MAN - the last person in the game.
# He took me THREE GOES to get standing right and it was the same model every
# time. The .glb version is T-posed with his arms straight out. The .obj is
# the one with the pose I wanted, and I kept assuming I had to rotate his arm
# in code on top of that - which gave him a twitching arm that moved every
# frame. I finally measured the .obj properly and his arm is ALREADY held
# forward in the file. So the posing code is off and the model is left alone.
FRIEND_MODEL   = 'confrontationman_armsdown'
FRIEND_IS_OBJ  = True          # the .obj, not the .glb. This matters.
FRIEND_TEXTURE = 'confman_0'   # the fallback if a material is not in the list
FRIEND_MODEL_H = 0.70          # measured off the file

FRIEND_POSE_ARM      = False   # <- leave this OFF. See above.
FRIEND_POINT_FORWARD = 90.0    # only used if the posing is ever turned on
FRIEND_POINT_DOWN    = 0.0
# these came from slicing the model and printing the numbers. It is 0.705
# tall and runs from x -0.115 to 0.149.
FRIEND_SHOULDER_X    = 0.055   # past this sideways is arm, not torso
FRIEND_SHOULDER_Y    = 0.44    # about 62% of the way up him
FRIEND_ARM_REACH     = 0.095   # shoulder to fingertips

FRIEND_TEXTURES = {
    'material_0': 'confman_0',
    'material_1': 'confman_1',
    'material_2': 'confman_2',
    'material_3': 'confman_3',
    'material_4': 'confman_3',
    'material_5': 'confman_4',
}

FRIEND_ARM_DROP = (8.0, 57.0, -40.0, 19.0)   # unused now the posing is off
FRIEND_HEIGHT  = 1.72        # so he stands eye to eye with me

# HOW BIG THE THING YOU SHOOT AT IS, as opposed to how big he looks. I made
# this much bigger than he is on purpose - wider than his shoulders, taller
# than his head. The last beat of the game is a choice, not a test of aim,
# and having to land a precise shot on a man standing still while he talks at
# you is the wrong kind of difficulty. It is invisible and he is alone in that
# end of the room, so nothing is lost by cheating here.
FRIEND_HITBOX  = Vec3(2.0, 2.40, 1.6)
FRIEND_POS     = Vec3(-1.0, 0, 1.6)   # he stands in my flat, between me and
                                      # the door. Out past the desk so he is
                                      # never standing inside the furniture

# the garden, parked far away from everything. The only way here is walking
# out of the door in the finale.
GARDEN_OFFSET = Vec3(0, 0, 600)

# THE PLOT - the empty land, set up so a model can be dropped in later.
ROOM_PLOT_NAME  = 'THE PLOT'
ROOM_PLOT_GLB   = 'the_plot'          # <- the file to drop in
ROOM_PLOT_SCALE = 1.0
ROOM_PLOT_UNLIT = True                # one draw state, no lighting maths
ROOM_PLOT_GRID  = 0.5                 # metres per baked collision cell
ROOM_PLOT_STAND_MAX = 3.0             # ignore surfaces higher than this
ROOM_PLOT_WALLS = True                # seal it, whatever the model left open

# where you land. Defaults to the old garden's spawn so nothing changes until
# i drop a model in.
ROOM_PLOT_SPAWN = GARDEN_OFFSET + Vec3(0, 2, 35)
ROOM_PLOT_FACE  = 0

# the door back out to the village. Press E and the rest of the game carries
# on as normal.
ROOM_PLOT_DOOR_AT   = GARDEN_OFFSET + Vec3(11.0, 0.1, 31.0)   # its FLOOR, not
                                                              # its middle
ROOM_PLOT_DOOR_SIZE = (4.5, 4.0)      # bigger than the village doors because
                                      # the garden is built at a larger scale
ROOM_PLOT_DOOR_TEX  = 'grandma4'      # the FOR SALE door
ROOM_PLOT_DOOR_YAW  = None            # None = turn to face the spawn

# THE HOUSE YOU GET IF YOU KILL NOBODY.
# Two files for one building: the pretty one you look at, and a much simpler
# one i only use for the collision. Building a collider out of the detailed
# house would be thousands of triangles for no benefit at all - you cannot
# feel the difference between a detailed wall and a flat one when you bump
# into it.
FANTASY_HOUSE_GLB   = 'fantasy_wooden_house'
FANTASY_HOUSE_OBJ   = 'fantasy_wooden_house_collision.obj'
FANTASY_HOUSE_SCALE = 1.0
FANTASY_HOUSE_UNLIT = True     # same as everything else - no lights in this game

# the collision file has a marker cube in it showing where the house should
# stand. Any triangle entirely past this z is that cube, and i throw it away
# once its position has been read - otherwise you bump into an invisible box
# in the middle of the garden.
FANTASY_HOUSE_CUBE_CUT = -9.5
FANTASY_HOUSE_CUBE_AT  = Vec3(-0.1741, 0.0, -10.5721)

# the house is turned all the way round so its front faces the way you walk
# in from. Otherwise you arrive looking at the back of it.
FANTASY_HOUSE_YAW = 180
FANTASY_HOUSE_AT  = Vec3(-0.1741, 0.05, 45.5721)
# that y of 0.05 is the TOP of the grass, not the grass itself. The grass
# sits at 0.02 and is scaled by 0.06, so its surface - the bit you actually
# stand on - is at 0.05. Put the house at 0.02 and it sinks into the lawn.

# the THANKS picture, hung on the back wall so you walk in and it is facing
# you rather than having to turn around and find it.
FANTASY_HOUSE_ART       = 'bathroom_bloodTHANKS'
FANTASY_HOUSE_ART_AT    = (-2.275, 2.50)   # x and y in the model's own units
FANTASY_HOUSE_ART_WIDE  = 1.05             # metres. The clean part of the
                                           # picture is 1.05 wide
FANTASY_HOUSE_ART_Z     = 4.255            # the wall itself is at 4.33, so
                                           # this floats just in front of it
FANTASY_HOUSE_ART_BOARD = 'darkwood'       # a board behind it, so it reads as
                                           # hung rather than painted on

# the spawn is set again here rather than edited above, so the original
# garden values stay readable further up
ROOM_PLOT_SPAWN = GARDEN_OFFSET + Vec3(0.0, 2.0, 35.0)
# facing 0 means looking along +z, which is at the FRONT of the house - but
# only because of the 180 turn above. Change that turn and change this too.
ROOM_PLOT_FACE  = 0


# ==================================================================
# THE SCRIPT - all dialogue and ending text
# ==================================================================

CHAPTERS = [

    # Broken into boxes rather than one wall, because the text box
    # pages on E and a briefing reads better delivered a beat at a time.
    [
        "Hey cringe lord, take your meta glasses off im talking to you.",
        "You are finally back from your 5k in 20 minutes, I heard you lost your job as a “Train Pusher”.",
        "We at Grey Matter Technologies offer you an exclusive opportunity for a real job, we have a bunch of weirdos waiting to be gunned down, who decided to rewire themselves to a 90s game."
        "Get rid of them for me.",
        "The handler has specified that due to the low cost of life, the "
        "specified business men have cash for about three or four "
        "reconstructions - so you may have to complete the job a couple of "
        "times. But you will be alright.",
        "Just remember you are broke. So you have one chance.",
        "Get right on the job. Or if you are still depressed, talk to some of "
        "the sane village residents - most of them do not even leave the "
        "house. Some talk about divine interference and stuff. I am not "
        "really into it, but you seem like the kind of guy.",
        "Get the job done. Make sure you kill them. CALIBARISTICS hired our "
        "guys to take care of it and we do not get the patent from the UN to "
        "seal the weapons deal otherwise.",
        "Also - I heard there is some du-je selling a house in the village. "
        "Try and bargain a mortgage with him and I am sure you will find "
        "yourself.",
    ],

    # The old chapters 0 to 3 were a different game - a man confessing about
    # having made a DOOM mod in his bedroom. That is not the story any more so
    # i took them out. These are the same voice as the first call: Grey Matter
    # Technologies, in writing, about work.
    [
        "Hello, wake up, we would like to offer... oh, you are still alive...",
        "Well then, go on then we aren't done here.",
        "Apparently there is something about the 640x800 resolution the people in there really like.",
        "Do not engage with that. I've read the forums, they are just nerds.",
        "I figured you must have the right mindset, to one day be a CEO yourself,",
        "three or four are left, so do not be sentimental about it, we'll talk about your payment later.",
    ],

    [
        "Since you have been doing good for the company...",
        "CALIBARISTICS offers you an exclusive opportunity if you finish the job.",
        "a house, 25 square meters, garbage truck thursdays, HBO subscription, of course only if you manage to kill the higher-ups.",
        "you smell like shit, have you been talking to the villagers? Whatever they'll tell you about morality, ",
        "don't listen, there is always gonna be people whining, but they just don't put in the effort to be a top ranking perssonell.",
        "I like the spines guy to be fair, an honest living is not something you see much around here anymore. ",
        "GOSH HAVE YOU BEEN TALKING TO JAKE? I can smell the Scummy Socialist through the phone!!!",
        "Get on the job...",
    ],

    [
        "Good Job, little heads-up.",
        "Someone redacted all the files, but theres... something else in this room. ",
        "This thing has been rebuilt more times than the records can show, I RECCOMMEND, you kill the little guys and get out of there.",
        "I don't even know if that thing is killable.",
        "If you do manage to kill it, there is... no conceavable 10 year plan that could... predict the power you may stumble onto.",
        "KILL THE MANAGERS, the CEO is just not a part of the job.",
    ],

    # This is the one that used to be "you are meant to die here". You are
    # not meant to die here any more - you are meant to SURVIVE it, so what
    # he says over it had to change too. See LEVELS[4]['survive'].
    [
        "Due to your over-achieving and not being a corporate friendly team-player the Grey Matter Technologies have let you go... ",
        "I'm keeping the money, good luck in there.",
        "You are too much of a psycopathic killer to deserve a property anyway, only calculated businessmen can have such assets.",
        "Anyway, if you have time fill out the feedback form and the service team will get back to you.",
        "please perish, and we appreciate the ease of competition you have provided to us.",

    ],
]

# ==================================================================
# THE HANDLER, AND THE ONLY TWO THINGS YOU CAN DO
# ==================================================================
FINALE_EXTRA_DOOR = False

FINALE_LINES_PACIFIST = [
    "Hey idiot",
    "You managed to kill... no one? We'll I'm honestly just disappointed",
    "Do you know what CALIBARISTICS do to a supplier who misses a delivery? "
    "Neither do I, when the beat drops I'm gonna probably game-end myself",
    "You are not getting the money, it's biometric",
    "You would have to kill me to get it, but I'll just be reincarnated, keep living your meaningless life alone you weirdo.",
    "Kill me already.",

]

FINALE_LINES = [
    "oh...",
    "uhm... Grey Matter Technologies would like to congratulate you on your achievements and...",
    "promote you to senior intern assistant service foreign co-partner manager.",
    "If you wish to accept please walk out, you will never get the money for the house otherwise."
    "look...",
    "The moneys biometrically bind to me, and if you kill me the feds will be onto you in a couple hundred years when they get to it anyway ",
    "make your choise loser, you are a depression nerd anyway.",
]

# YOU SHOT HIM. THE MONEY IS YOURS.
ENDING_KILL = [
    "...",
    "Biometric. He did say.",
    "The transfer clears, four hundred a life... Grey Matter Technologies thanks you for your co-work and participation in the survey. ",
    "weirdos...",
    "There is a house at the end of the road with FOR SALE painted on the door, it's yours go an claim it",
]

# YOU LET HIM KEEP IT. THAT IS THE END OF THAT.
# The losing ending, and i did not want it to feel like a punishment - it is
# just the ordinary consequence of never having been paid. Walked out with
# clean hands and nothing else.
ENDING_LEAVE_PACIFIST = [
    "You let him live",
    "Idiot...",
    "He does not follow you. He is already on the phone with somebody talking about a new opening for an exclusive job",
    "Outside is the same road, The same weird sky, weird villagers, The door at the end still says FOR SALE",
    "Somebody in this village has been waiting years for a true Divine malice, a Divine Light that has not yet been shattered by the disgust of this world...",
    "The Scientist. The Nerd. He wants to speak to you, its urgent!",
]

# THE SCIENTIST SIGNS
# What he says when you come back having killed nobody. He is the one who has
# been going on about non-knowledge and divine light since the first time you
# met him, and this is the only proof he is ever going to get. He is my
# favourite one to write for.
SCIENTIST_LEASE = [
    "Four times in a place built to make killing cheap, Grey Matter orchestrated the whole thing,",
    "they just wanted to have a face to blame it on.",
    "Do you understand what that is? That is not restraint. Restraint is a structure, you have preserved your humanity, and therefore you have entangled your divine light!",
    "I must confess...",
    "I am one of the 3 eternal trigons who created this world, I bestow upon you... Life",
    "Meaning... You've got a light, you can feel it on your back a light, you can feel it on your back, don't look back",
    "A person should learn to detect and watch that gleam of light which flashed across his mind from within, more than the lustre of the firmament",
    "of the bards (poets) and sages (philosophers) from the ancients up to the present...",
    "You aren't perfect, but Trust thyself: every heart vibrates to that iron string. - 'Self Relience' - Ralph Waldo Emerson ",

]

# Each one is a LIST OF LINES rather than one block, and the box pages anything
# too tall for it on top of that - so they read a line at a time and none of it

# KILLED YOUR WAY THROUGH IT, took his money, got the lease from the DJ
ENDING_EMPEROR = [
    "Don't be fooled, it is not over yet you have simply reached THE BEST PART, ",
    "by choosing to not follow down a path of GOLDEN AGE you have truly eradicated all sense of laziness.",

    "Now, you will not get sucked into a single existence, with the cost of life being so incredibly low THERE IS TRULY A POINT in wasting your life now.",

    "Go out and find your way in this AUTOMATOID FLESH, you have persevered, "

    "live your life in a recently signed and sealed contract, bought, real, signed, no mortgage, rent free, 25 square meters, house, in a residential area,",
    "free of landlords and monthly check-ups, no electricity bill, alone, weekly garbage trucks, TRULY AN ETERNAL MALICE.",

    "Although you will be forever trapped in your boundless blues, as the CEO of yourself,",
    "you will forever lack knowledge and understanding, the past is ever present, you will be trapped forever.",
    "The sun smiles at you and you are overwhelmed with rotten husk, boundless power. You may have the soul of an emperor...",
    "but you weep and stink of the worst thing that you always swore you would not become.",

    "Set goals, have a resolution, have a ten year plan, work quarterly, invest, wake up early, have a boundless optimal mindset.\n\nGood luck",
]

# KILLED NOBODY, the scientist signed, the old house
ENDING_OCEAN = [
    "In the deepest ocean, your eyes, they turn me, they tell me, they say to me.",
    "Why should I stay here, after all, why should I stay. I would be crazy not to follow, follow where you lead,",
    "your eyes, they tell me. Turn me on to phantoms, I follow to the edge of the earth, and fall off.",
    "You are not to blame for, Bittersweet distractors, Dare not speak its name",
    "Dedicated to all human beings, because we separate like ripples on a blank shore",
    "Everybody would, Everybody leaves, if they get the chance, a way out and this, this is my chance, i get eaten by the worms, and weird fishes, ",
    "picked over by the worms and weird fishes, i hit the bottom, i hit rock bottom and escape.",
    "Blown out speakers, Fireworks and hurricanes, rainbows and butterflies, I'm not here, This isn't happening, I never really got there, I just...",
    "pretended that I had, You've got a light, you can feel it on your back a light, you can feel it on your back",
]

# KILLED THE BOSS : THE CEO OF THE UNIVERSE
# This one interrupts the level. Full screen picture, the speech, then black,
# then the menu - see Game.ending_ceo.
CEO_PICTURE = 'lifepictureENDING'
CEO_BLACK_AFTER = 3.0        # seconds of black before the menu
ENDING_CEO = [
    "You have DEVOURED the CEO of the UNIVERSE, who has bestowed upon you a "
    "glimpse of his power, the CEO has something to say to you.",

    "The living organism, in a situation determined by the play of energy on "
    "the surface of the globe, ordinarily receives more energy than is "
    "necessary for maintaining life.",

    "It has come to my attention that, without profit, it must be spent, "
    "willingly or not, gloriously or catastrophically.",

    "The layers have been peeled off one by one, it comes to us all, How come "
    "I end up where ive started with you, how come i end up where i went "
    "wrong, you become a condensed balance of operations, a rotation of 38 "
    "degrees.",

    "You killed the sound\n\nRemoved backbone A pale imitation With the edges "
    "sawn off. Blink your eyes\n\nOne for yes Two for no They got a skin and "
    "they put you in",

    "Oh, the lines wrapped 'round your face are now for everyone else to see. "
    "YOU ARE TRULY ALIVE.",

    "The ultimate trauma loop of, the one who seeked to destroy the matter of "
    "which themselves is brought up on, there is nothing left for you other "
    "than a pity of trauma in endless grace of power.",
]

# THE ONE YOU BOUGHT WITH HIS MONEY
# Door 5. The one that said FOR SALE and 2 LIVE(R)S the entire game.
ENDING_BOUGHT = [
    "The sign came down this morning. Somebody took it down before you got "
    "here, which means somebody was told.",
    "Two lives, it said. You brought seventeen and his as well.",
    "It is a good house. Twenty five square metres. No landlord, no monthly "
    "check-ups, bins on a Thursday.",
    "There is a fridge in the corner that is not plugged in and you are not "
    "going to plug it in.",
    "Have a look round. It is yours. Nobody is going to ring.",
]

# AND STANDING IN IT
# The scientist's one. This is the suburban house that has been in the
# project since the very beginning, not the flat - so the lines are about
# arriving somewhere rather than about the room you already knew.
ENDING_OWNED = [
    "You did not walk here. One moment the drawer, then the grass.",
    "The picture of the house is still on the wall. You could take it down. "
    "You are not going to take it down.",
    "There is a fence. There is a kitchen with the tiles somebody chose. "
    "There are three pictures of somebody's grandmother on the wall.",
    "Twenty five square metres. Bins on a Thursday. No alarm in the morning "
    "unless you set one.",
    "You did not have enough capital to be reincarnated.\n\nYou had enough "
    "not to need to be.",
]

ENDING_LEAVE = [
    "You let him keep it.",
    "He does not gloat. He is already looking at his phone. You were a line "
    "item and the line is closed.",
    "Outside, the road is the same road. The door at the end of it still says "
    "FOR SALE and it still says two lives.",
    "You have done the work of about eleven of them and you cannot afford one.",
    "The alarm will go off again in the morning. It always does. Somebody will "
    "have something that needs doing.",
    "You did not have enough capital to be reincarnated as a man with a house.",
]

# SIGNING THE LEASE
# The last beat of the walk-out ending: you left him standing there and went
# and did the paperwork. The DJ's line here is mine, straight out of the
# document.
ENDING_LEASE = [
    "You came back. Most people do not come back.",
    "When the beat drops, I get premium access, high speeds and no ads for "
    "five dollars a month. That is my arrangement. This one is yours.",
    "Sign there. And there. Twenty five square metres, residential, no "
    "landlord, no monthly check-ups, no electricity bill, bins on a Thursday.",
    "Bought. Real. Signed. Rent free.\n\nAlone.",
    "Congratulations. You have simply bought a room.",
]

# THE OLD TWO-LINE ENDING_LEAVE WAS HERE and it was overwriting the new one.
# It sat further down the file than the replacement, so Python assigned mine
# and then immediately assigned the old one over the top of it - which is the
# quietest kind of wrong there is, because everything still runs.

# THE THIRD ENDING IS GONE.
# There used to be a secret one - pick the phone up one more time and find
# out it was always you, one man doing both voices. That belonged to the
# story this used to be. I wanted only two options at the end and the old
# dialogue gone, so it is gone: the list and the function that showed it have
# both been deleted, and nothing in the file reaches for them any more.


# ==================================================================
# LEVEL TABLE - what each DOOM level contains
# ==================================================================
SURVIVE_SECONDS = 45        # seconds to last out on the last level
SURVIVE_MESSAGE = 'you have been bamboozled'
SURVIVE_OBJECTIVE = 'do not die, reminder: you are poor'

# 'mix' IS A WEIGHTING, NOT A COUNT
# How MANY enemies a level has is decided by the map - rooms x per_room, plus
# corridors - so these numbers do not have to be kept in step with anything.
# They are the odds of each type: 'weak': 42, 'runner': 14 means three
# quarters of this level's garrison are shamblers and a quarter are runners.
# Keeping the old numbers means the mixes i had already tuned still come out
# the same.
#
# 'alive' is only used by level 5 now, as the ceiling on how big the endless
# wave is allowed to get.
LEVELS = [
    dict(title='Team leaders, Supervisors (hard working employees)',
         mix={'weak': 42, 'runner': 14},
         per_room=4, corridors=6,   alive=28, toughness=1.00,
         voice_in_level=False, winnable=True),

    dict(title='Middle Management',
         mix={'weak': 49, 'casual': 25, 'runner': 18},
         per_room=4, corridors=8,   alive=35, toughness=1.10,
         voice_in_level=False, winnable=True),

    dict(title='Vice Presidents',
         mix={'weak': 42, 'casual': 35, 'strong': 18, 'runner': 21, 'mystery': 11},
         per_room=5, corridors=10,  alive=42, toughness=1.20,
         voice_in_level=False, winnable=True),

    dict(title='President council and Senat of Human Resources ',
         mix={'casual': 42, 'strong': 35, 'runner': 25, 'mystery': 18, 'secret': 11},
         # thinner overall (it was 5 per room and 12 corridors) because
         # BOSS_CROWD adds eight more around him - so the level is emptier
         # everywhere except his end of it, which is where i wanted them
         per_room=3, corridors=6,   alive=49, toughness=1.35,
         voice_in_level=True,  winnable=True, boss=True),

    dict(title='CEO-s',
         mix={'weak': 49, 'casual': 49, 'strong': 42, 'runner': 35,
              'mystery': 31, 'secret': 18},
         per_room=6, corridors=16,  alive=60, toughness=1.60,
         # not unwinnable any more - survivable. Stay alive for
         # `survive` seconds and the exit unlocks itself.
         survive=SURVIVE_SECONDS,
         voice_in_level=True,  winnable=False),
]

# THE LAST LEVEL IS SURVIVABLE NOW
# It used to kill you on purpose after 75 seconds and that was the only way
# out of it. Now it is a SURVIVAL: last this long and a way out appears.
# LEVELS[4]['survive'] is the number that actually matters; i keep this one
# because a few older lines still refer to it.
UNWINNABLE_TIMEOUT = 45


# Quiet jazz under the DOOM levels. Low enough that it sits behind the
# gunfire rather than competing with it, loud enough that you notice it and
# it bothers you slightly - which is the whole point of putting a drum groove
# under a massacre.
DOOM_MUSIC      = 'jazz_groove'
DOOM_MUSIC_VOL  = 0.10

# ==================================================================
# LEVEL TABLE - extra
# ==================================================================

# THE MP3 IS NOT A PROBLEM, but it did need code rather than just a
# filename, and it is worth knowing why before i swap any other sound.
RING_SOUND      = 'iphone_alarm'   # the phone on the desk
RING_VOLUME     = 1.85
RING_LOOP       = True             # an alarm loops. False = one ring per beat
RING_FADE_WITH_DISTANCE = True     # quieter as you walk away from the desk
# If what i meant was the MENU music, this is the line to change - the
# loader is the same one, so 'iphone_alarm' works here too.
#
# THE MENU MUSIC IS MINE NOW. It was 'living organism audio'; it is
# 'ulasturkish' instead, it loops for as long as the title screen is up, and
# it stops the moment you press PLAY. That last part is not new - _set_menu()
# has always started and stopped this clip with the menu, so "only during the
# main menu" was already true and stays true. The old file is still in the
# project; put the name back and it works.
MENU_MUSIC_FILE = 'ulasturkish'
MENU_VOLUME = 0.50
# How many frames must actually be DRAWN before the title music starts.
# FRAMES, not seconds - see MenuMusicStarter. 8 is about a seventh of a
# second on a machine running at 60, and it is the first moment the menu is
# genuinely on screen rather than still being built. Doing this on a timer
# instead of on frames is what made the music start over a black screen.
MENU_MUSIC_WAIT_FRAMES = 8
AUDIO_TYPES = ('.mp3', '.ogg', '.wav', '.flac',
               '.midi', '.opus')

# ==================================================================
# HOW IT DECIDES, AND WHY IT IS NOT WIRED INTO THE DOORS
# ==================================================================
AMBIENCE_ON = True
# scene -> (sound file, volume). Anything not listed here is silent.
AMBIENCE_TRACKS = {
    'apartment': ('apartmentsound', 0.30),   # the hellish one. Quiet.
    'office':    ('villagesound',   0.22),   # 'office' IS the village
    # 'finale' is deliberately absent - see the note above
}
AMBIENCE_FADE = 1.2        # seconds to fade in and out, so nothing clicks
AMBIENCE_TICK = 0.25       # how often it checks. Not every frame.
# ---- LOUDNESS ----
# the voices always have to be louder than the music. ambience is 0.22-0.30 and the voices are 0.70-0.90, and the ambience ducks while anybody is speaking
AMBIENCE_DUCK = 0.45       # what the ambience drops to while anyone talks
AMBIENCE_DUCK_SPEED = 3.0  # how quickly it ducks and comes back

# ---- THE EVENING GRADE IS GONE ----
# i did not like it so the constants, the class and the instance are all deleted rather than switched off. eveninggrain.png is still on disk, nothing loads it

HANDLER_VOICE_ON  = True
NPC_VOICE_ON      = True
# Per-chapter recordings (voice_0.wav, voice_1.wav ...). None of them
# exist in the project, so this is False and the lookup - and its two
# warning lines per phone call - is skipped. See VoicePlayer.play().
CHAPTER_VOICE_FILES = False
HANDLER_VOICE_VOL = 0.85       # him. The phone, the DOOM level, the finale.
NPC_VOICE_VOL     = 0.70       # everybody else. Quieter - they are not him.

# time we talk to him it's slightly more pitched up, which I think is
# interesting."
HANDLER_VOICE_STAGES = [
    'ulasturkishCEOhandlerVOICE',
]

# ==================================================================
# THIS TABLE IS EMPTY AND THAT IS NOT AN OVERSIGHT. The seven files did
# ==================================================================
HANDLER_CHAPTER_VOICES = {
    0: '1handler',      # 56s
    1: '2handler',      # 21s
    2: '3handler',      # 31s
    3: '4handler',      # 23s
    4: '5handler',      # 20s
}
HANDLER_FINALE_PACIFIST_VOICE = '6handler'   # the zero-liver confrontation
HANDLER_FINALE_VOICE          = '7handler'   # the ordinary one

# TO THE END ALL THE WAY THROUGH AND ALWAYS LOOP - no stops between the
# texts. Do that for all the handler voice lines."
HANDLER_VOICE_PLAYS_THROUGH = True

# Everybody who is not him. This is the FALLBACK - the voice an NPC uses when
# they have not been given a recording of their own.
#
# ---- IT IS THE HANDLER'S FILE NOW ----
# I wanted the normal npcs to use the same file as the handler voice line, so
# the default NPC voice is ulasturkishCEOhandler rather than ulasturkishPC.
# The old file is still in the project - put the name back and nothing else
# has to change.
NPC_VOICE_STAGES = [
    'ulasturkishCEOhandlerVOICE',
]

# ==================================================================
# AND THEN LOOP UNTIL THE CHATTING IS ENDED BY THE PLAYER, not like it
# ==================================================================
NPC_VOICE_LOOPS_UNTIL_CLOSE = True


# THE DEATH SCREENS
# You die in any way at all - shot, punched, stood in the sludge, fell out of
# the world - and one of these three fills the screen, with the control
# picture in the middle as the button back to the menu and one line of comic
# sans in a colour picked at random.
DEATH_SCREENS       = ['deathscreen1', 'deathscreen2', 'deathscreen3']
# HOW MUCH THE PICTURE IS ALLOWED TO STRETCH. 0 = no distortion at all, so a
# portrait picture gets blown up until it covers the screen and the sides are
# cropped off. 1 = squashed to exactly the screen shape, which on
# deathscreen1 (493 x 674, taller than it is wide) was grotesque when i tried
# it. 0.35 is "a bit stretched but not too much": the picture always fills
# the screen, it just meets it a third of the way rather than being cropped
# the whole way.
DEATH_STRETCH       = 0.35
DEATH_BUTTON_IMAGE  = 'controlredfinal'   # the control picture, as the button
DEATH_BUTTON_HEIGHT = 0.30                # fraction of the screen height
DEATH_BUTTON_POS    = (0.0, -0.02)        # dead middle, as asked
DEATH_LINES = [
    'you did not have enough capital to be reincarnated',
    'you did not have enough funds to be put back together',
    'the flesh automaton that you are, did not have enough currency to be '
    'turned back into a moving thing',
]
# Rainbow, deliberately awful, same palette family as the menu paragraphs.
DEATH_TEXT_COLOURS = [
    RGB(255, 60, 190), RGB(90, 255, 90),  RGB(255, 230, 40),
    RGB(60, 200, 255), RGB(255, 120, 20), RGB(190, 90, 255),
    RGB(255, 255, 255), RGB(255, 40, 40), RGB(40, 255, 210),
]
DEATH_TEXT_SCALE = (1.25, 1.85)      # picked at random inside this range
DEATH_TEXT_WRAP  = 42                # characters before it wraps
DEATH_TEXT_SPOTS = [(0.0, 0.33), (0.0, -0.33)]   # over or under the button
# THIS IS OFF, AND IT USED TO BE ON.
# It meant "dying on the last level carries the story on", which was right
# when that level was unwinnable and dying there WAS the ending. The last
# level is a survival now: last ninety seconds and a door opens. If dying
# still handed you the finale then surviving would be pointless - so death is
# death, and the only way to meet him is to get out alive.
DEATH_STORY_DEATH_CONTINUES = False
# WHERE THE BUTTON SENDS YOU on an ordinary death. 'menu' is what i wanted -
# the run is over, press the control picture, start again. 'retry' puts you
# back at the start of the level you died on, which is what it used to do.
DEATH_RETURNS_TO = 'menu'

# THE TEXT BOX
# One box, on the right of the screen, wearing one of my stretched pngs with
# the textbox outline drawn over the top of it. EVERYTHING that is words from
# a living thing or from the world goes through it: the men on the benches,
# the five house NPCs, THE HANDLER on the phone, the open-the-door prompt and
# the ESC-to-close-the-ads notice.
TALK_FRAME_IMAGE = 'textbox'          # the outline, drawn OVER the background
TALK_BG_PREFIX   = 'textbox_bg'       # anything starting with this is a back-
                                      # ground and gets picked at random
# only used if not one textbox_bg image is in the project, so the box is
# never an empty rectangle
TALK_BG_FALLBACK = ['ribcage', 'guts', 'nerves', 'red_marble',
                    'crungewallpaper', 'purple_carpet', 'randomrainbow']
# The frame png is 1677 x 1062, and its hole - which i measured off the file
# rather than guessing - runs from 3.7% to 96.8% across and 6.1% to 94.9%
# down. The box below keeps that shape and the text is inset by TALK_PAD,
# which is a hair more than the hole so nothing can touch the drawn border.
TALK_BOX_ASPECT  = 1677 / 1062
# THE FONT IS TWICE THE SIZE. Nothing the randomness touches is changed -
# only bigger. TALK_TEXT_SCALE is doubled and the name plate grew with it.
TALK_BOX_WIDTH   = 0.66               # fraction of the SCREEN WIDTH
TALK_BOX_HEIGHT  = TALK_BOX_WIDTH / TALK_BOX_ASPECT
TALK_BOX_MARGIN  = 0.030              # gap from the right edge of the screen
TALK_BOX_Y       = 0.05               # high enough that the small box fits
                                      # underneath it and the head fits above
# The outline is drawn OVER the background picture, so its middle has to be
# transparent - the textbox.png i use has had its middle knocked out for
# exactly this. If i ever swap in a SOLID one, set this False and the outline
# gets drawn behind instead, with the background inset into its hole.
TALK_FRAME_OVER  = True
TALK_PAD_X       = 0.075              # fraction of the box eaten by the border
TALK_PAD_Y       = 0.105
TALK_TEXT_SCALE  = 1.44               # was 0.72, exactly twice
TALK_WRAP        = 22                 # characters per line inside the box
TALK_MAX_LINES   = 8                  # taller than this and it pages
TALK_NAME_SCALE  = 0.95               # the name plate grew with it
TALK_TEXT_COLOUR = RGB(20, 14, 10)    # dark, because the backgrounds are pale
TALK_NAME_COLOUR = RGB(120, 20, 20)
TALK_SHADOW      = RGB(255, 240, 210, 190)   # a bright ghost behind the text,
                                             # so it survives a busy picture
TALK_SHADOW_OFF  = 0.0035
TALK_SCRIM       = 90                 # 0-255 of dark laid over the background
                                      # picture. 0 shows my png raw.
# The words appear a few at a time rather than all at once. E finishes the
# line early; E again moves on. False = the whole line lands instantly.
TALK_TYPEWRITER  = True
TALK_TYPE_SPEED  = 70.0               # characters a second
TALK_FREEZE_LOOK = False              # True = you cannot turn while it is up

# THE SMALL BOX UNDERNEATH, same skin, for everything that is not a person
# talking: [E] prompts, warnings, the advert instructions.
PROMPTS_IN_BOX    = True
PROMPT_BOX_WIDTH  = 0.46              # bigger font, bigger box
PROMPT_BOX_HEIGHT = PROMPT_BOX_WIDTH / TALK_BOX_ASPECT
PROMPT_BOX_GAP    = 0.030             # under the big box
PROMPT_TEXT_SCALE = 1.0              # was 0.62
PROMPT_WRAP       = 20
NOTICE_SECONDS    = 3.4               # how long a warning stays up

# ==================================================================
# YOU CAN NEVER FALL OUT OF A LEVEL AGAIN
# ==================================================================
FALL_GUARD_ON   = True
FALL_LIMIT      = 12.0     # metres below the spawn before it catches you
FALL_GUARD_TICK = 0.50     # how often it looks
FALL_GUARD_COOLDOWN = 5.0  # silence after a rescue, so it can never
                           # teleport you again before you have landed. This
                           # is the number that stops it freezing you.
FALL_GUARD_GIVE_UP = 3     # rescues in a row in one scene before it decides
                           # the floor is genuinely missing and stops
FALL_MESSAGES = [
    "beep boop code error sorry",
    "I really have no idea how you even got there",
    "I must have tripped, because of the META glasses",
    "I think I saw god there for a second",
    "you weren't supposed to get here",
]
FALL_MESSAGE_SCALE = 2.0

OOB_ON            = True
OOB_MARGIN        = 2.5               # metres past the edge before it fires
OOB_MESSAGE       = "you weren't supposed to get here"
OOB_REPEAT        = 6.0              # seconds before it will say it again
OOB_TICK          = 0.50              # how often it looks (not every frame)
# IT PUTS YOU BACK NOW.
# OutOfBounds used to notice you had left the map and print a line about it,
# and that was all - you just stayed out there, which was useless. This makes
# it a wall rather than a comment: past the margin and you get returned to
# the last spot you were safely standing on. See the OutOfBounds class.
OOB_RETURN_YOU    = True

# ==================================================================
# GETTING THROUGH THE WALLS
# ==================================================================
# My own complaint about this was: "why is it so easy to get past colliders,
# it's so easy to get out of the map or get stuck between stuff... it happens
# in the village and in the doom level."
#
# There are THREE separate faults and they need three separate fixes. It is
# worth knowing which is which, because from inside the game they look
# identical, and only one of them is about the colliders at all.
#
# ---- FAULT 1 : YOU MOVE FURTHER THAN YOU CHECK ----
# On a long frame the controller moves you the whole distance in one go and
# only tests for a wall at the end of it, so a thin wall can be stepped
# straight through. The fix is to chop the movement into pieces no longer
# than MOVE_SUBSTEP_MAX and test each one.
MOVE_SUBSTEP_ON   = True
MOVE_SUBSTEP_MAX  = 0.16      # metres between collision checks. The rays are
                              # 0.5m, so this is a 3x safety margin.
MOVE_SUBSTEP_CAP  = 12        # never more than this many checks in one frame,
                              # so a two second freeze cannot lock the game up
                              # trying to simulate all of it at once

# ---- FAULT 2 : NOTHING PUTS YOU BACK ----
# Once you were out, you were out. FallGuard caught you falling but only
# below the floor; walking out sideways across the fields got noticed and
# then allowed anyway. See OOB_RETURN_YOU above.

# ---- FAULT 3 : WEDGED BETWEEN TWO THINGS ----
# in a corner one of the two rays always hits, and the controller refuses to move you AT ALL when one does, so you cannot walk out
#
# THE FIX: hold a movement key and go nowhere for UNSTICK_SECONDS and you get lifted slightly and pushed back towards open ground
UNSTICK_ON        = True
UNSTICK_SECONDS   = 0.9       # holding a key and going nowhere for this long
UNSTICK_DISTANCE  = 0.35      # ...where "nowhere" is less than this, in total
UNSTICK_LIFT      = 0.45      # how far up it lifts you to clear a lip
UNSTICK_PUSH      = 0.75      # how far back towards open ground it slides you

# ---- AND ONE MORE : THE WALLS SWITCH ON TOO LATE ----
# WALL_COLLIDER_RADIUS was 16m with a 0.35s tick. Sprinting at 10 m/s you
# cover 3.5m between two ticks, so a wall could still be non-solid when you
# arrived at it if you came round a corner into it. 26m and a faster tick
# costs a few more boxes and removes the last way through.
# (The number itself is set up further up - i put this note here so all four
# faults are written down in one place instead of scattered about.)

# The one on the phone. His face turns over and over in the corner while he
# talks, with the text box beside it carrying what he is saying - the two are
# on screen together, which is the whole point.
HANDLER_NAME        = 'THE HANDLER'
HANDLER_HEAD_IMAGE  = 'bosshandler'
HANDLER_HEAD_HEIGHT = 0.23        # fraction of the screen. Noticeable, small.
# HOW IT TURNS. Three of them, change the word:
#   'spin'   turns on the vertical axis, so the face swings away, goes edge
#            on, and comes back - a head rotating in place. This is the one
#            i use.
#   'roll'   spins in the plane of the screen like a wheel, always fully
#            visible, never edge on.
#   'sweep'  turns left and right through HANDLER_SWEEP degrees and back,
#            never all the way round - the least silly of the three.
HANDLER_SPIN_MODE   = 'spin'
HANDLER_SPIN_SPEED  = 490.0       # degrees a second
HANDLER_SWEEP       = 90.0        # only used by 'sweep': 90 either way = 180
HANDLER_HEAD_PLATE  = True        # his name under the head
# his lines go in the text box beside the head, instead of being
# thrown across the screen in three-word bursts. False brings the scattered
# comic sans back - the burst code is untouched, it is just not called.
VOICE_IN_TALK_BOX   = True

# WHAT THE LIVING THINGS SAY
# The whole of the writing job is this one table: a name, and a list of
# boxes. Replace a list and that character changes, and nothing else in the
# file has to know about it.
#
# The five are indexed by ROOM, which is the door number minus one: door 1 ->
# room 0, door 4 is the DJ, and door 5 is my own house.
VILLAGE_VOICES = [
    "A point in the horizon. A melting scene from your childhood. Your "
    "mortality is showing, by the way. Just so you know.",

    "I must be sleeping. Is this real? I heard the 640 by 480 was handed "
    "down to us by the gods. It lets you see the unseen.\n\n"
    "Huh. Are you even human? Say what you like - this place is intensely "
    "beautiful.",

    "I cannot turn myself off any more. Not from life. Specifically not from "
    "the online part, which is where my sense of being worth anything sits "
    "now.\n\n"
    "I need a clean page as much as I need a backbone to show up to work "
    "with. I need to reply fast as much as I need eight hours.",

    "Funny thing - I feel most relaxed at night. The chase stops and the only "
    "thing left to lose is sleep. And tomorrow's productivity.\n\n"
    "Losing tomorrow's does not bother me nearly as much as losing the "
    "feeling of having done enough today.",

    "Once you work out what your options actually are, you settle. And then "
    "you can see the next ten years from where you are standing.\n\n"
    "That is the part that frightens me. Not that it is bad. That it is "
    "already visible.",

    "The bittersweet distractors. That is what they are. Social media and the "
    "desire-producing machines of the entertainment industry, and I am "
    "deeply affected by both and I know it.",

    "They calculate it, you know. Levels of colour, sounds, smiling faces, "
    "how much it looks like food or a small animal.\n\n"
    "Straight into your perception. So that what you want gets redirected "
    "somewhere it can be charged for.",

    "Games are the worst of it. The most total. Built straight out of "
    "Skinner's boxes - press the lever, get the pellet, press it again.\n\n"
    "You are pressing one now. I am not judging. I am in it too.",

    "This society is frozen. Perpetuated. Like the chrysalis of a corpse "
    "butterfly.\n\n"
    "It suggests you could grow. It does not permit growth past the limits "
    "the thing itself set.",

    "Have you noticed the colours out here? Nothing matches. Nothing is "
    "textured like the thing it is meant to be.\n\n"
    "I have stopped reading the street as a place to buy things in. Now it is "
    "just space, and I go across it however I like.",

    "The layers get peeled off one at a time. It comes to us all. Soft as "
    "your pillow, et cetera, et cetera.",

    "How come I end up where I started. How come I end up where I went "
    "wrong.\n\n"
    "I will not take my eyes off the ball again. Then they reel you out and "
    "cut the string anyway.",

    "Blink once for yes. Twice for no. Go on, check me for a pulse - I am "
    "genuinely not certain.",

    "Everything I own is a subscription. Including, I suspect, the part of me "
    "that minds about that.",

    "I do not leave the house. I want to be clear that this is a decision and "
    "not a condition. Everyone believes me, which is the worst part.",

    "Some of them round here talk about divine interference. Light coming "
    "through, that sort of thing.\n\n"
    "I am not really into it. But you look like the kind of man who might be.",

    # THE HOUSE AT THE END OF THE ROAD
    # The gossip, and my running joke about what a life is worth. The last
    # door in the village has FOR SALE painted on it and 2 LIVE(R)S under
    # that, and everybody in the place has an opinion about it.
    "Have you heard there is a place for sale down there? Two lives, they are "
    "asking.\n\nOr livers. They did not specify. Crazy how high the prices "
    "have got recently, am I right?",

    "Two lives for twenty five square metres. When I was your age you got a "
    "whole terrace for one and they threw in the reconstruction.",

    "It has been for sale a while. Nobody local can afford it and nobody who "
    "can afford it wants to live next to us.",

    "The going rate on a life is four hundred, before tax. So the house is "
    "eight hundred. So the house is nothing.\n\nSo what am I doing.",

    "Mercenary work is just work now. My cousin does it. Respectable, good "
    "hours, and they put you back together after.\n\nTwice, usually. Three "
    "times if you are insured.",

    "You are one of the gun men, aren't you. No - it is fine. Somebody has to, "
    "and the pay is honest. Which is more than I can say for the shop.",
]

# The named ones. Room index = door number minus one; door 4 is the DJ and
# door 5 is the house you are trying to buy.
#
# ---- WHO HAS A RECORDING, AND HOW IT BEHAVES ----
# One row per room. The keys are the same room numbers NPC_LINES uses.
#
#     voice   the file, without its extension
#     loop    True  = go round again if the conversation outlasts the clip
#             False = PLAY ONCE, all the way through, then silence
#
# I wanted both behaviours, and which one each of these gets is down to how
# the recording is meant to work:
#
#   JAKE          loop=True.  it should play start to finish until the
#                 player presses esc or reaches the final line - so it must
#                 not run out on a slow reader.
#   THE SCIENTIST loop=False. this one plays once and stops.
#   THE DJ        loop=False. same, it fully plays out and that is it.
#
# A room with no row here uses the shared NPC voice, looping, as before.
ROOM_VOICES = {
    0: dict(voice='scientistFULLMONOLOGUE', loop=False),   # THE SCIENTIST
    2: dict(voice='JaakSASSfinal',          loop=True),    # JAKE
    3: dict(voice='DJmonologue',            loop=False),   # THE DJ
}
# NOTE ON THE FILENAME: it is "JaakSASSfinal.wav", with two a's - not
# "JakeSASSfinal". The real filename is what has to be used here, so if i
# ever rename the file i have to change this line with it.

# ==================================================================
# WHY THE MP3s ARE NOW .ogg
# ==================================================================
ROOM_MUSIC = {
    0: ('scientistmusic', 0.16),   # the scientist. The quietest of the four.
    1: ('depressionnap',  0.30),   # the liver shop
    2: ('chunkopops',     0.24),   # Jake. Louder than the scientist, as asked.
    3: ('rainDJ',         0.28),   # the DJ
}
ROOM_MUSIC_FADE = 1.0              # seconds to fade in and out

# THE BOSS ENDING'S VOICE NOTE
# Plays once, and the ending waits for it - see Game.wait_for_boss_voice().
BOSS_ENDING_VOICE = 'bosskillSASSfinal'
BOSS_ENDING_TAIL  = 1.5    # a breath of silence after it before the fade
BOSS_ENDING_FALLBACK = 108.0   # only used if panda3d will not report the
                               # clip's length. 108s is what the file is.

# My own text, word for word, split into four boxes at the paragraph breaks i
# wrote. Nothing has been reworded - the only thing done to it is the
# splitting.
SCIENTIST_FIRST = [
    "You must be the depressed loner renting that weird apartment, let me "
    "tell you, don't take these people too seriously, most of them have "
    "been put together hundreds of times and they barely have any coherent "
    "thoughts left between their ears.",

    "You'll get no advice from me with that liver count - come back when "
    "you have 0 livers harvested and I'll have something to say to you, "
    "meanwhile have this point of thought - I recorded it when I was still "
    "a scummy Grey Matter Worker like you, so mind the voice.",

    "I'm just saying... there is a way out you know, you can choose a "
    "different path.",

    "The more we act on behalf of others the more we bewilder ourselves. "
    "We no longer exist as mountains but sanddunes, happy to shift on any "
    "demanding winds of an ocean.\n\n"
    "For each new shape we are rewarded but we are also destroyed, after "
    "some 85 years we are at risk to die with knowledge but with a missing "
    "volume of our selves. Our souls remain a mystery.",
]

NPC_LINES = {
    # room 0 is the corridor, and door 2 opens it - the nerd scientist
    0: ('THE SCIENTIST', [
        "The more we act on behalf of others, the more we bewilder "
        "ourselves.\n\n"
        "We stop being mountains and become sand dunes. Happy to shift on "
        "whatever wind is demanding something today.",

        "For each new shape we are rewarded. And for each new shape we are "
        "destroyed a little.\n\n"
        "After eighty-five years of it you die full of knowledge with a whole "
        "volume of yourself missing.",

        "Emerson had it, you know. A person should learn to watch that gleam "
        "of light which flashes across his own mind from within.\n\n"
        "More than all the poets and philosophers put together. Trust "
        "thyself. Every heart vibrates to that iron string.",

        "Though the wide universe is full of good, no kernel of nourishing "
        "corn can come to a man except through the work he does on the plot "
        "of ground given to him to till.\n\n"
        "I have a plot. It is twenty five square metres.",

        "Do not see yourself as a finished item. That is the whole of it. "
        "That is the only useful thing I know.",
    ]),
    # room 1 is the shop, and door 1 opens it - the man behind the counter
    1: ('THE ORGAN SELLER', [
        "Spines. That is what is in today. Spines and a bit of liver.",

        "Prices are up, mind. A place down the road is going for two lives. "
        "Or livers - they did not specify and I did not ask.",

        "little word of advice, You are doing the same job I am.",
        "You just get to use a gun for it, "
        "and you do not have to keep yours refrigerated.",

    ]),
    2: ('JAKE', [
        "I am Jake. I pulsate. I laugh. I crawled, I conquered. I am the "
        "chief security officer of this village.",

        "Chaos is imaginary. Time is a frigid crystal of perfect order - from "
        "any point in it you can trivially calculate any other.\n\n"
        "There are only so many steps you can rotate it through in your head, "
        "mind you.",

        "My job is pointless, because security is inherent in everything. "
        "Some people disagree with me. Those people are depressed.\n\n"
        "I mostly drink coffee and take video calls.",
    ]),
    3: ('THE DJ', [
        "Hey Flesh. I could smell you from outside.",

        "When the beat drops, I get premium spotify access, high speeds and no ads "
        "for five dollars a month.\n\n"
        "That is the current arrangement. ",

        "I hear you are in the market for an affordable 25 sqare meters house",

        "you gotta get a lease for that though, litte word of advice"
        "try going around sparing a few lives and you might just find yourself in a better spot\n\n"
        "The handler is not offering you a reward, it is a mortgage with a body attached to it.",

        "Look... just do what he says but, try and spare the lives of those weirdos,",
        "meanwhile listen to some hip-beats and doom scroll.",
    ]),
}
NPC_LINES_DEFAULT = ('SOMEBODY', [
    "There is nothing behind my eyes and I would like you to leave.",
])
NPC_TALK_RANGE = 2.2        # how close E reaches for a person, in metres

# How many of the pool an unnamed person says before they run out. Drawn on
# the spot, so the same bench guy is not the same conversation twice.
VILLAGE_VOICE_COUNT = (2, 4)


def random_village_lines(seed=None):
    rng = random.Random(seed) if seed is not None else random
    n = rng.randint(*VILLAGE_VOICE_COUNT)
    pool = list(VILLAGE_VOICES)
    rng.shuffle(pool)
    return pool[:n]
NPC_TALK_RANGE = 3.2        # how close E reaches for a person, in metres


# ==================================================================
# HELPERS - finding assets, textures, sound
# ==================================================================
def _asset_root():
    from pathlib import Path as _AssetPath          # not relying on the star import
    if getattr(sys, 'frozen', False):               # True only inside the .exe
        packed = getattr(sys, '_MEIPASS', None)
        if packed:
            return _AssetPath(packed)
        return _AssetPath(sys.executable).resolve().parent   # --onedir fallback
    return application.asset_folder


ASSETS = _asset_root()


IMAGE_TYPES = ('.png', '.jpg', '.jpeg', '.bmp', '.tga')

# FOLDERS THE ASSET SCAN WILL NOT GO INTO
# The scan walks the whole project once at startup, which is what lets me
# move any file anywhere without breaking anything. The only folders it must
# NOT walk are the ones with tens of thousands of files that could never be
# an asset: a virtual environment is about 30,000 files on its own and would
# turn a half-second startup into thirty.
#
# This matters more than it looks now that the launcher can sit in the
# project root - see launcher.py - because from there the project root IS the
# asset folder and .venv is right next to it.
#
# 'build' IS THE BIG ONE, AND IT WAS MISSING. A previous PyInstaller run
# leaves build/ and dist/ behind, and they contain a COMPLETE SECOND COPY of
# every asset in the project. Counted on this project:
#
#     whole tree                      21,890 files
#     without build/ and .venv/        5,699 files
#
# So anything walking the tree was doing four times the work it needed to,
# and finding stale copies of my own files while it was at it - which is its
# own quiet bug, because find_asset() returns the first match. Editing a
# texture and seeing no change in game is exactly what that looks like.
SKIP_FOLDERS = {'.venv', 'venv', '.git', '.idea', '__pycache__', 'node_modules',
                'site-packages', 'dist', '.pytest_cache', 'exportToHTML',
                'build', '_unused'}


def _skip(path):
    try:
        parts = path.relative_to(ASSETS).parts
    except ValueError:
        parts = path.parts          # not under the root at all - test the lot
    return any(part in SKIP_FOLDERS for part in parts)


_image_index = None        # 'STARTAN3' -> Path, built once. See build_image_index.


def build_image_index():
    global _image_index
    if _image_index is not None:
        return _image_index
    _image_index = {}
    clashes = []
    started = time.time()
    try:
        for f in ASSETS.rglob('*'):
            if f.suffix.lower() not in IMAGE_TYPES or _skip(f):
                continue
            key = f.stem.upper()
            if key in _image_index:
                clashes.append(key)
                continue
            _image_index[key] = f
    except Exception as exc:
        print('!! could not index the project images (%s) - falling back to '
              'searching the whole tree every time, which is slow' % exc)
    print('images: %d indexed in %.2fs (one walk instead of one per texture)'
          % (len(_image_index), time.time() - started))
    if clashes:
        uniq = sorted(set(clashes))
        print('   (%d duplicate image names, first found wins: %s%s)'
              % (len(uniq), ', '.join(uniq[:8]),
                 ' ...' if len(uniq) > 8 else ''))
    return _image_index


def find_image(folder, stem):
    target = stem.upper()
    if folder and folder.exists():
        for f in folder.iterdir():
            if f.suffix.lower() in IMAGE_TYPES and f.stem.upper() == target:
                return f
    return build_image_index().get(target)


_file_index = None         # 'adam.obj' -> Path, built once


def build_file_index():
    global _file_index
    if _file_index is not None:
        return _file_index
    _file_index = {}
    try:
        for f in ASSETS.rglob('*'):
            if _skip(f):
                continue
            key = f.name.lower()
            if key not in _file_index:
                _file_index[key] = f
    except Exception as exc:
        print('!! could not index the project files (%s)' % exc)
    return _file_index


def find_asset(*names):
    for name in names:
        direct = ASSETS / name
        if direct.exists():
            return direct
        found = build_file_index().get(name.lower())
        if found is not None:
            return found
    return None


# ==================================================================
# THE ONE THING TO BE CAREFUL OF
# ==================================================================
URSINA_PRIMITIVES = {
    'quad', 'cube', 'sphere', 'plane', 'circle', 'cone', 'cylinder',
    'diamond', 'arrow', 'line', 'wireframe_cube', 'wireframe_quad',
    'icosphere', 'sky_dome', 'arrow_down', 'file_icon',
}


def install_fast_model_loader():
    try:
        from ursina import mesh_importer as _mi
        from ursina import entity as _ent
    except Exception as exc:
        print('!! could not speed up the model loader: %s' % exc)
        return False
    if getattr(_mi, '_eternalmalice_fast', False):
        return True
    _original = _mi.load_model
    TYPES = ('.bam', '.ursinamesh', '.obj', '.glb', '.gltf', '.blend')

    def fast_load_model(name, path=None, *args, **kwargs):
        try:
            if isinstance(name, str):
                stem = name.split('.')[0]
                # already loaded once - ursina's own cache is faster than us
                if (stem not in _mi.imported_meshes
                        and stem.lower() not in URSINA_PRIMITIVES):
                    types = (('.' + name.split('.', 1)[1],)
                             if '.' in name else TYPES)
                    for suffix in types:
                        hit = find_asset(stem + suffix)
                        if hit is not None:
                            return _original(name, hit.parent, *args, **kwargs)
        except Exception:
            pass          # anything unexpected: fall through to ursina
        if path is None:
            return _original(name, *args, **kwargs)
        return _original(name, path, *args, **kwargs)

    # entity.py did `from ursina.mesh_importer import load_model`, which binds
    # the function itself - so patching the module alone would miss it.
    _mi.load_model = fast_load_model
    _ent.load_model = fast_load_model
    _mi._eternalmalice_fast = True
    return True


install_fast_model_loader()


_folder_index = None


def find_folder(name):
    global _folder_index
    direct = ASSETS / name
    if direct.is_dir():
        return direct
    if _folder_index is None:
        _folder_index = {}
        try:
            for f in ASSETS.rglob('*'):
                if _skip(f) or not f.is_dir():
                    continue
                key = f.name.lower()
                if key not in _folder_index:
                    _folder_index[key] = f
        except Exception as exc:
            print('!! could not index the project folders (%s)' % exc)
    return _folder_index.get(name.lower())


_texture_cache = {}


# THE ADVERTS REALLY WERE THE PROBLEM
#     textbox              1677 x 1062   1.8 Mpixel, on screen for every line
#     monthlysubscription  1401 x  875   1.2 Mpixel
#     watermark            1597 x  176
#     lifecourse            825 x  627
#     perfectbody           456 x  960
#
# A UI quad a quarter of the screen wide does not need a 1677 pixel source -
# it gets downsampled to a few hundred pixels on the way to the screen
# anyway, so all that extra resolution buys me is memory bandwidth and
# texture cache misses. I generate halved copies as <name>_low.png and every
# one of these names is looked up as _low FIRST, exactly the way the sky
# textures already work. My originals are untouched and still on disk.
#
# Add a name here and it gets the same treatment automatically, as long as a
# matching _low file exists.
UI_DOWNSCALE = {'TEXTBOX', 'MONTHLYSUBSCRIPTION', 'WATERMARK', 'LIFECOURSE',
                'PERFECTBODY', 'HOUSE100', 'GREENIEFACE', 'LOSER0',
                'DEATHSCREEN1', 'DEATHSCREEN2', 'DEATHSCREEN3',
                'CONTROLREDNECKMAN', 'DONTYUHAVEENOUGH',
                'lifegame', 'HUMANSUPREMACY', '2AC1D15A38C5B17BE7458C43EFAA5967'}
# ==================================================================
# POTATO MODE
# ==================================================================
# the note on TEXTURE_DETAIL up in SECTION 1 says what the levels are
def texture_detail_scale():
    return TEXTURE_DETAIL_LEVELS.get(str(TEXTURE_DETAIL).lower(), 1.0)


_detail_saved = [0, 0]     # pixels before, pixels after - for the report


def load_texture_scaled(path, extra=1.0):
    k = texture_detail_scale() * max(0.01, extra)
    if k >= 0.999:
        return Texture(str(path))
    try:
        from PIL import Image
        with Image.open(path) as im:
            im = im.convert('RGBA')
            w = max(TEXTURE_MIN_PX, int(im.width * k))
            h = max(TEXTURE_MIN_PX, int(im.height * k))
            _detail_saved[0] += im.width * im.height
            _detail_saved[1] += w * h
            return Texture(im.resize((w, h), Image.NEAREST))
    except Exception as exc:
        print('!! could not shrink %s (%s) - loaded full size'
              % (getattr(path, 'name', path), exc))
        return Texture(str(path))


def crunchy_texture(folder, stem, detail=1.0):
    key = (str(folder), stem.upper(), round(detail, 3))
    if key in _texture_cache:
        return _texture_cache[key]
    # the half-size copy first for the handful of enormous UI images
    # see UI_DOWNSCALE. Falls straight through to the original if there is no
    # _low file, so deleting them all just makes the game heavier again.
    path = None
    if stem.upper() in UI_DOWNSCALE:
        path = find_image(folder, stem + '_low')
    if path is None:
        path = find_image(folder, stem)
    tex = None
    if path:
        try:
            tex = load_texture_scaled(path, detail)   # potato mode + per-room
            tex.filtering = None          # None = nearest neighbour = crunchy
        except Exception as e:
            print('texture failed:', stem, e)
    _texture_cache[key] = tex
    return tex


def safe_texture(name):
    try:
        return load_texture(name)
    except Exception:
        return None


def safe_audio(name, **kwargs):
    try:
        a = Audio(name, **kwargs)
        # Ursina hands back a silent object if the clip is missing
        if getattr(a, 'clip', None) is None:
            return None
        return a
    except Exception:
        return None


# LOADING A SOUND THAT IS NOT A .WAV
class Sound:
    def __init__(self, sound, name, path):
        self._sound = sound
        self.name = name
        self.path = path

    def play(self, restart=True):
        try:
            if restart:
                self._sound.stop()
            self._sound.play()
        except Exception:
            pass

    def stop(self):
        try:
            self._sound.stop()
        except Exception:
            pass

    @property
    def playing(self):
        try:
            # 2 is AudioSound.PLAYING on every panda3d
            return self._sound.status() == 2
        except Exception:
            return False

    @property
    def length(self):
        try:
            return float(self._sound.length())
        except Exception:
            return 0.0

    @property
    def volume(self):
        try:
            return self._sound.getVolume()
        except Exception:
            return 0.0

    @volume.setter
    def volume(self, v):
        try:
            self._sound.setVolume(max(0.0, min(1.0, float(v))))
        except Exception:
            pass

    @property
    def loop(self):
        try:
            return bool(self._sound.getLoop())
        except Exception:
            return False

    @loop.setter
    def loop(self, on):
        try:
            self._sound.setLoop(bool(on))
        except Exception:
            pass


_sound_cache = {}


def load_sound(stem, loop=False, volume=1.0, quiet=False):
    if stem in _sound_cache:
        return _sound_cache[stem]
    path = find_asset(*[stem + ext for ext in AUDIO_TYPES])
    if path is None:
        if not quiet:
            print('!! sound %r not found - looked for %s anywhere in the '
                  'project' % (stem, ' / '.join(stem + e for e in AUDIO_TYPES)))
        _sound_cache[stem] = None
        return None
    sound = None
    try:
        # ==================================================================
        # PANDA3D DOES NOT USE OPERATING SYSTEM PATHS. It has its own path
        # ==================================================================
        try:
            from panda3d.core import Filename
            panda_path = Filename.fromOsSpecific(str(path))
        except Exception:
            panda_path = str(path)
        sound = application.base.loader.loadSfx(panda_path)
    except Exception as exc:
        print('!! panda3d could not load %s (%s)' % (path.name, exc))
    if sound is None:
        print('!! %s was found but could not be decoded.' % path.name)
        if path.suffix.lower() == '.mp3':
            print('!! panda3d\'s audio manager on this machine has no mp3 '
                  'decoder. Convert it once and everything works:')
            print('!!     ffmpeg -i "%s" "%s.ogg"' % (path, path.with_suffix('')))
            print('!! (drop the .ogg next to the .mp3 - load_sound tries ogg '
                  'as well and will pick it up with no code change)')
        _sound_cache[stem] = None
        return None
    clip = Sound(sound, stem, path)
    clip.loop = loop
    clip.volume = volume
    print('sound: %s loaded (%.1f KB, %s)'
          % (path.name, path.stat().st_size / 1024,
             'looping' if loop else 'one shot'))
    _sound_cache[stem] = clip
    return clip


# The constants and the whole explanation are up in SECTION 3b next to
# HANDLER_VOICE_STAGES. This is the small amount of machinery.

# which rung of HANDLER_VOICE_STAGES he is on. Goes up by one every call.
handler_voice_step = 0


def load_voice(stem):
    return load_sound(stem, loop=True, volume=1.0)


def handler_voice_clip(chapter=None, finale=None):
    if not HANDLER_VOICE_ON:
        return None
    want = None
    if finale == 'pacifist':
        want = HANDLER_FINALE_PACIFIST_VOICE
    elif finale == 'normal':
        want = HANDLER_FINALE_VOICE
    elif chapter is not None:
        want = HANDLER_CHAPTER_VOICES.get(chapter)
    if want:
        got = load_voice(want)
        if got is not None:
            return got
        print('!! handler: %r is in the table but not in the project - '
              'falling back to the shared voice' % want)
    return handler_voice_ladder()


def handler_voice_ladder():
    if not HANDLER_VOICE_ON:
        return None
    if not HANDLER_VOICE_STAGES:
        return None
    step = handler_voice_step
    if step >= len(HANDLER_VOICE_STAGES):
        step = len(HANDLER_VOICE_STAGES) - 1
    return load_voice(HANDLER_VOICE_STAGES[step])


def handler_voice_step_up():
    global handler_voice_step
    handler_voice_step = handler_voice_step + 1


def npc_voice_clip(which=0):
    if not NPC_VOICE_ON:
        return None
    if not NPC_VOICE_STAGES:
        return None
    if which >= len(NPC_VOICE_STAGES):
        which = 0
    return load_voice(NPC_VOICE_STAGES[which])


def start_voice_clip(clip, volume, loop=True):
    if clip is None:
        return
    clip.loop = bool(loop)
    clip.volume = volume
    clip.play()


def stop_voice_clip(clip):
    if clip is None:
        return
    clip.stop()


def stop_all_voice_clips():
    for stem in HANDLER_VOICE_STAGES:
        stop_voice_clip(load_voice(stem))
    for stem in NPC_VOICE_STAGES:
        stop_voice_clip(load_voice(stem))
    # every recorded line an NPC might have been reading out
    for stem in ALL_NPC_LINE_CLIPS:
        stop_voice_clip(load_voice(stem))


# The table and the whole explanation are in SECTION 3b next to
# AMBIENCE_TRACKS. This is the small amount of machinery it needs: one entity
# that asks where you are four times a second and plays the loop that belongs
# to that room. That is genuinely all it is.
class Ambience(Entity):
    def __init__(self):
        super().__init__()
        self.tick = 0.0
        self.playing_name = None     # which FILE is up, by stem
        self.playing_volume = 0.0
        self.clip = None
        self.level = 0.0             # where the fade currently is, 0..1
        self.duck = 1.0              # 1 = nobody talking, AMBIENCE_DUCK = talking

    def wanted_track(self):
        if not AMBIENCE_ON:
            return None
        if game is None:
            return None
        if _menu_open:
            return None              # the title screen has its own music
        if game.state == 'house':
            return ROOM_MUSIC.get(getattr(game, 'house_room', None))
        # THE HAPPY ENDING has its own track. Only that one ending - every
        # other route into the garden falls through to the table below and
        # gets whatever it got before, which is nothing.
        if game.state == 'ending' and getattr(game, 'happy_ending', False):
            return (HAPPY_ENDING_MUSIC, HAPPY_ENDING_VOLUME)
        return AMBIENCE_TRACKS.get(game.state)

    def somebody_is_talking(self):
        if talk_box is not None and talk_box.open:
            return True
        if voice is not None and voice.playing:
            return True
        return False

    def update(self):
        # the fade and the duck are smooth, so they run every frame
        want_duck = AMBIENCE_DUCK if self.somebody_is_talking() else 1.0
        self.duck = lerp(self.duck, want_duck,
                         min(1, time.dt * AMBIENCE_DUCK_SPEED))

        self.tick -= time.dt
        if self.tick <= 0:
            self.tick = AMBIENCE_TICK
            self.choose_track()

        # fade toward on or off
        target = 1.0 if self.playing_name else 0.0
        step = time.dt / max(0.05, AMBIENCE_FADE)
        if self.level < target:
            self.level = min(target, self.level + step)
        elif self.level > target:
            self.level = max(target, self.level - step)

        if self.clip is None:
            return
        if self.level <= 0.001 and not self.playing_name:
            stop_voice_clip(self.clip)
            self.clip = None
            return
        self.clip.volume = self.full_volume() * self.level * self.duck

    def full_volume(self):
        return self.playing_volume

    def choose_track(self):
        # want is (file stem, volume) or None. The FILE STEM is the identity
        # of a track - not which table it came from - so a house and a scene
        # can both supply one and this still knows whether anything changed.
        want = self.wanted_track()
        want_name = want[0] if want else None

        if want_name == self.playing_name:
            return                   # already right, nothing to do

        # a different room. Stop what is on and start what belongs.
        if self.clip is not None:
            stop_voice_clip(self.clip)
            self.clip = None
        self.level = 0.0
        self.playing_name = want_name
        self.playing_volume = want[1] if want else 0.0
        if want_name is None:
            return
        self.clip = load_sound(want_name, loop=True, volume=0.0)
        if self.clip is None:
            print('!! ambience: %s not found, so that room will be silent'
                  % want_name)
            self.playing_name = None
            return
        self.clip.loop = True
        self.clip.volume = 0.0
        self.clip.play()


ambience = Ambience()


# ==================================================================
# THIS IS WHY THE GAME GOT SLOWER THE LONGER IT RAN
# ==================================================================
# ----------------------------------------------------------------------
# The thing i kept noticing: every minute that passes the game gets a bit
# slower, and even the easy to run places end up laggy. It is not the
# textures, the village or potato mode. It is this.
#
# ursina's own ursfx() - the thing every beep, gunshot and hurt noise in this
# game goes through - does this, and I have read the source to be sure:
#
#     def ursfx(...):
#         a = Audio(wave, loop=True, ...)      # a NEW ENTITY, every call
#         a.animate(...) x4                    # four Sequences, every call
#         invoke(a.stop, delay=...)            # and it only ever STOPS it
#
# It never destroys it. An ursina Audio is an Entity, and every Entity lives
# in scene.entities, which the engine walks once per frame forever. So every
# single shot you fire leaves a dead sound object behind for the rest of the
# session, and the per-frame loop gets one step longer. Fire a minigun for
# thirty seconds - fourteen rounds a second - and you have left four hundred
# corpses in the update loop. That is your progressive slowdown exactly.
#
# THE FIX is one line: destroy it once it has finished playing. SFX_LIFETIME
# is how long we let it live first, and it is deliberately generous - the
# clip has already stopped by then, this is only about reclaiming the object.
#
# The counter is printed by F if you want to watch it: it should sit at a
# handful and come back down, not climb forever.
SFX_LIFETIME = 1.0        # seconds before a one-shot sound is reclaimed
# made, cleaned up, LEAKED - just so it can be reported. The third number is
# new and it is the one that matters: see the docstring on play_sfx().
_sfx_made = [0, 0, 0]


def play_sfx(curve_points, volume=0.5, wave='sine', pitch=0, pitch_change=0,
             speed=1.0):
    points = list(curve_points)
    while len(points) < 5:
        points.append(points[-1])

    try:
        a = ursfx(points, volume=volume, wave=wave, pitch=pitch,
                  pitch_change=pitch_change, speed=speed)
    except Exception as exc:
        _sfx_made[2] += 1
        if _sfx_made[2] in (1, 10, 100, 1000):
            print('!! a procedural sound failed and may have leaked (%s). '
                  'That has happened %d times. play_sfx pads the curve to '
                  'five points to stop exactly this - see its docstring.'
                  % (exc, _sfx_made[2]))
        return None
    _sfx_made[0] += 1
    try:
        # destroy() takes a delay, so this costs one scheduled call and hands
        # the entity back to Python the moment the sound is over
        destroy(a, delay=SFX_LIFETIME)
        _sfx_made[1] += 1
    except Exception:
        pass
    return a


def beep(pitch=-8, length=0.25, wave='sine', volume=0.5):
    play_sfx([(0.0, 1.0), (length * 0.6, 0.9), (length, 0.0)],
             volume=volume, wave=wave, pitch=pitch, pitch_change=0, speed=1.0)


def shoot_sound():
    play_sfx([(0.0, 0.0), (0.1, 0.9), (0.15, 0.75), (0.3, 0.14), (0.6, 0.0)],
             volume=0.5, wave='noise',
             pitch=random.uniform(-13, -12), pitch_change=-12, speed=3.0)


def hurt_sound():
    play_sfx([(0.0, 1.0), (0.2, 0.4), (0.4, 0.0)],
             volume=0.6, wave='noise', pitch=-20, pitch_change=-6, speed=1.6)


# ==================================================================
# MODEL LOADING - the .obj and .glb readers
# ==================================================================

# Direction the fake sunlight comes from, for flat shading. Purely cosmetic. completely useless
SHADE_LIGHT = Vec3(0.35, 0.86, -0.37).normalized()
SHADE_AMBIENT = 3.55


def flat_shade(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    wx, wy, wz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length < 1e-9:
        return 1.0
    facing = abs((nx * SHADE_LIGHT.x + ny * SHADE_LIGHT.y + nz * SHADE_LIGHT.z) / length)
    return SHADE_AMBIENT + (1.0 - SHADE_AMBIENT) * facing


def pose_friend_arm(v):
    if not FRIEND_POSE_ARM:
        return v
    x, y, z = v
    # only the RIGHT arm. +x is his right as the model is authored; if it
    # turns out to be his left, negate this test and the model is mirrored.
    if x < FRIEND_SHOULDER_X:
        return v
    reach = x - FRIEND_SHOULDER_X
    if reach <= 0:
        return v
    # 0 at the shoulder, 1 at the fingertips
    t = min(1.0, reach / max(0.001, FRIEND_ARM_REACH))
    ang = math.radians(FRIEND_POINT_FORWARD) * t
    drop = math.radians(FRIEND_POINT_DOWN) * t
    # about the shoulder, in the Y/Z plane - forward is -z in the model's
    # own space, which is the direction the player stands in
    dy = y - FRIEND_SHOULDER_Y
    dz = z
    ny = dy * math.cos(ang) - dz * math.sin(ang)
    nz = dy * math.sin(ang) + dz * math.cos(ang)
    # then let it fall a little, if asked
    ny2 = ny * math.cos(drop) + nz * 0.0
    return (x, FRIEND_SHOULDER_Y + ny2, nz)


def bend_arms_down(v, cfg):
    sx, sy, deg, reach_len = cfg
    x, y, z = v
    reach = abs(x) - sx
    if reach <= 0:
        return v
    side = 1.0 if x > 0 else -1.0
    t = min(1.0, reach / max(0.001, reach_len))   # 0 at shoulder, 1 at fingers
    ang = math.radians(deg) * t * side
    dx, dy = x - sx * side, y - sy
    ca, sa = math.cos(ang), math.sin(ang)
    return (sx * side + dx * ca - dy * sa, sy + dx * sa + dy * ca, z)


def load_obj_by_material(obj_path, scale=1.0, origin=(0, 0, 0), flip_v=False,
                         flip_x=True, drop_triangle=None, shade=False,
                         bend_arms=None, pose=None):
    verts, raw, uvs, groups = [], [], [], {}
    current = 'Default'
    ox, oy, oz = origin
    sx = -1.0 if flip_x else 1.0

    with open(obj_path, 'r', errors='ignore') as f:
        for line in f:
            if line.startswith('v '):
                p = line.split()
                x, y, z = float(p[1]), float(p[2]), float(p[3])
                raw.append((x, y, z))
                if bend_arms:
                    x, y, z = bend_arms_down((x, y, z), bend_arms)
                # `pose` is any f(vertex) -> vertex. I use it to point the
                # confrontation man's arm at you - see pose_friend_arm().
                if pose is not None:
                    x, y, z = pose((x, y, z))
                verts.append(((sx * x - ox) * scale, (y - oy) * scale, (z - oz) * scale))
            elif line.startswith('vt '):
                p = line.split()
                u, v = float(p[1]), float(p[2])
                uvs.append((u, -v if flip_v else v))
            elif line.startswith('usemtl'):
                current = line.split(None, 1)[1].strip()
            elif line.startswith('f '):
                face = [t.split('/') for t in line[2:].split()]
                vlist, ulist, clist = groups.setdefault(current, ([], [], []))
                # fan-triangulate: works for triangles, quads and n-gons
                for k in range(1, len(face) - 1):
                    corners = (face[0], face[k], face[k + 1])
                    idx = [int(c[0]) - 1 for c in corners]

                    if drop_triangle and drop_triangle(*[raw[i] for i in idx]):
                        continue

                    if shade:
                        lit = flat_shade(*[verts[i] for i in idx])
                        tint = (lit, lit, lit, 1.0)

                    for c, vi in zip(corners, idx):
                        ti = int(c[1]) - 1 if len(c) > 1 and c[1] else -1
                        vlist.append(verts[vi])
                        ulist.append(uvs[ti] if 0 <= ti < len(uvs) else (0, 0))
                        if shade:
                            clist.append(tint)
    return groups


doors = []          # every individual door leaf, filled by build_doom_map
# The invisible walls and lid that stop you leaving the map. They are SOLID
# to the player and INVISIBLE to the navigation pass - see the note where
# they get built. Anything that asks "where is the floor" has to ignore
# these or it finds the roof instead, which is a mistake i made twice.
doom_bounds_boxes = []
# the rectangle you are allowed to be in, filled in by build_doom_map().
# (x0, x1, z0, z1, ceiling)
doom_play_area = None
# How thick the invisible boundary walls are. See the note where they are
# built: thin walls can be stepped straight through on a long frame, because
# collision tests where you ARE, not the path you took to get there.
DOOM_WALL_THICK = 4.0
# If i somehow get outside the play area anyway, this is how far back inside
# it i get put.
DOOM_PUSH_BACK = 1.5


def nav_ignore():
    return tuple([player] + doom_bounds_boxes)


def cluster_triangles(vlist, ulist, radius):
    cells = {}
    for t in range(0, len(vlist) - 2, 3):
        cx = (vlist[t][0] + vlist[t + 1][0] + vlist[t + 2][0]) / 3
        cy = (vlist[t][1] + vlist[t + 1][1] + vlist[t + 2][1]) / 3
        cz = (vlist[t][2] + vlist[t + 1][2] + vlist[t + 2][2]) / 3
        key = (int(cx // radius), int(cy // radius), int(cz // radius))
        cells.setdefault(key, []).append(t)

    seen, out = set(), []
    for key in cells:
        if key in seen:
            continue
        group, queue = [], [key]
        seen.add(key)
        while queue:
            k = queue.pop()
            group.append(k)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        n = (k[0] + dx, k[1] + dy, k[2] + dz)
                        if n in cells and n not in seen:
                            seen.add(n)
                            queue.append(n)
        lv, lu = [], []
        for k in group:
            for t in cells[k]:
                lv += [vlist[t], vlist[t + 1], vlist[t + 2]]
                lu += [ulist[t], ulist[t + 1], ulist[t + 2]]
        if lv:
            out.append((lv, lu))
    return out


def build_doom_map(parent):
    folder = ASSETS / DOOM_FOLDER
    obj = folder / DOOM_OBJ
    if not obj.exists():
        # The DOOM folder does not have to sit next to the launcher any more.
        # This was the one place in the file that used to insist on it, and it
        # is what stopped me moving the DOOM folder into assets/ with
        # everything else. Now it gets looked up like every other asset.
        found = find_asset(DOOM_OBJ)
        if found is None:
            print('!! could not find %s anywhere in the project' % DOOM_OBJ)
            print('!! the DOOM_E1M1 folder needs to be somewhere under', ASSETS)
            return None, []
        obj, folder = found, found.parent
        print('   DOOM map found at %s' % obj)

    groups = load_obj_by_material(obj, DOOM_SCALE, DOOM_ORIGIN, DOOM_FLIP_V)

    pieces = []
    every_vertex = []
    toxic_vertices = []          # the nukage, on its own
    doors.clear()
    for material, (vlist, ulist, _clist) in groups.items():
        if not vlist:
            continue
        # DOORS ARE NOT SOLID. They're left out of the collision mesh, so a
        # doorway is always walkable even if that particular leaf never lifts.
        if not any(d in material.upper() for d in DOOR_TEXTURES):
            every_vertex.extend(vlist)

        # DOOM's sky "flat" is a fake ceiling meaning open air. Hide it.
        if DOOM_HIDE_SKY_FLATS and material.upper() == 'F_SKY1':
            continue

        # the one unassigned group gets a real wall rather than flat grey
        tex = crunchy_texture(folder, material)
        if tex is None:
            tex = crunchy_texture(folder, DEFAULT_TEXTURE)
            if tex is not None:
                print(f'   {material}: no image of its own, using {DEFAULT_TEXTURE}')

        # A DOOR gets split into separate leaves so each can move on its own.
        if any(d in material.upper() for d in DOOR_TEXTURES):
            for leaf in cluster_triangles(vlist, ulist, DOOR_CLUSTER):
                lv, lu = leaf
                door = Entity(parent=parent,
                              model=Mesh(vertices=lv, uvs=lu, mode='triangle',
                                         static=True),
                              texture=tex, double_sided=True, unlit=True,
                              color=color.white if tex else RGB(90, 90, 95))
                door.material_name = material
                door.is_toxic = False
                door.rest_y = 0.0
                door.centre = Vec3(sum(v[0] for v in lv) / len(lv),
                                   sum(v[1] for v in lv) / len(lv),
                                   sum(v[2] for v in lv) / len(lv))
                doors.append(door)
                pieces.append(door)
            continue

        # THE DOOM MAP IS CHUNKED TOO
        # Exactly the same problem the village had. One entity per texture
        # means one bounding box per texture, and every one of those boxes
        # spans the whole map - so nothing could ever be culled and all 1,800
        # triangles plus 57 texture binds went through every single frame from
        # every position. Cut into DOOM_CHUNK-metre columns it culls properly,
        # and standing in one room stops paying for the other six.
        for _cv, _cu in chunk_triangles_xz(vlist, ulist, DOOM_CHUNK):
            mesh = Mesh(vertices=_cv, uvs=_cu, mode='triangle', static=True)
            piece = Entity(parent=parent, model=mesh, texture=tex,
                           double_sided=True,  # X was negated, so faces can flip
                           unlit=True,         # flat lowpoly, fog does the shading
                           color=color.white if tex else RGB(90, 90, 95))
            piece.material_name = material
            piece.is_toxic = any(t in material.upper() for t in TOXIC_TEXTURES)
            if piece.is_toxic:
                toxic_vertices.extend(_cv)
            pieces.append(piece)
        continue
        piece = Entity(parent=parent, model=None)
        piece.material_name = material
        # tag the sludge so ToxicFloors can find it later
        piece.is_toxic = any(t in material.upper() for t in TOXIC_TEXTURES)
        if piece.is_toxic:
            # keep a copy of the sludge's own triangles. See the note
            # where toxic_collision is built, below.
            toxic_vertices.extend(vlist)
        pieces.append(piece)

    # One collision mesh for everything, including the hidden sky flats so
    # you can't wander off the top of the map.
    collision = Entity(parent=parent,
                       model=Mesh(vertices=every_vertex, mode='triangle', static=True),
                       collider='mesh', visible=False)

    # It was not the texture names. 'NUKAGE' has always substring-matched
    # NUKAGE3, which is the only nukage material the exported map contains,
    global toxic_collision
    if toxic_vertices:
        toxic_collision = Entity(
            parent=parent,
            model=Mesh(vertices=toxic_vertices, mode='triangle', static=True),
            collider='mesh', visible=False)
        toxic_collision.is_toxic = True
        print('DOOM sludge: %d toxic triangles given their own collider - '
              'standing in it now actually hurts (%s)'
              % (len(toxic_vertices) // 3,
                 ', '.join(sorted({m for m in groups
                                   if any(t in m.upper() for t in TOXIC_TEXTURES)}))))
    else:
        toxic_collision = None
        print('DOOM sludge: no toxic materials found in the map at all - '
              'nothing to stand in. Looked for %s' % (TOXIC_TEXTURES,))

    # The .obj is an open shell: E1M1's outdoor bits have no roof and its outer
    # edges are unsealed, so a rocket jump or a bad step drops you out of the
    # world entirely. Four walls and a lid, sized from the geometry itself.
    if every_vertex:
        bx0 = min(v[0] for v in every_vertex); bx1 = max(v[0] for v in every_vertex)
        by1 = max(v[1] for v in every_vertex)
        bz0 = min(v[2] for v in every_vertex); bz1 = max(v[2] for v in every_vertex)
        pad, lid = 3.0, by1 + 6.0
        cx, cz = (bx0 + bx1) / 2, (bz0 + bz1) / 2
        w, d = (bx1 - bx0) + pad * 2, (bz1 - bz0) + pad * 2
        # THIS BOX IS WHY ENEMIES WERE SPAWNING ON THE ROOF
        # The navigation pass finds standable ground by firing rays downward
        # and asking what they hit. The lid of this box is a huge flat
        # horizontal surface with nothing above it, so it looked like the
        # best floor in the level - and the flood fill happily filled the
        # entire roof, which is where my enemies kept turning up.
        #
        # They get collected into doom_bounds_boxes and every navigation ray
        # now ignores them. They still stop YOU falling out of the world,
        # which is all they were ever for.
        #
        # ---- THE WALLS ARE THICK NOW ----
        # You could still squeeze out of the map in places, and a 1-metre
        # thick boundary wall is why. Panda3D's collision is not continuous:
        # it tests where you ARE, not the line between where you were and
        # where you are. Run at a thin wall on a frame that happens to be
        # long - a texture streaming in, an advert appearing - and you can
        # step from one side of it to the other in a single move without ever
        # being inside it. Nothing stops you, because you were never in the
        # wall. This took me a long time to understand and it is the same
        # fault as FAULT 1 up in SECTION 1, just on a different wall.
        #
        # Making them DOOM_WALL_THICK metres thick means a single frame's
        # movement can never span the wall, so there is always at least one
        # frame where you are inside it and get pushed out. It costs nothing:
        # they are invisible boxes.
        #
        # The push-back guard in DoomBoundsGuard is the second line of
        # defence, for the corners and for anything the box misses.
        doom_bounds_boxes.clear()
        t = DOOM_WALL_THICK
        for px, pz, sx, sz in ((bx0 - pad, cz, t, d + t * 2),
                               (bx1 + pad, cz, t, d + t * 2),
                               (cx, bz0 - pad, w + t * 2, t),
                               (cx, bz1 + pad, w + t * 2, t)):
            doom_bounds_boxes.append(Entity(
                parent=parent, model='cube', collider='box', visible=False,
                position=(px, lid / 2, pz), scale=(sx, lid + 12, sz)))
        # remember the playable rectangle so the guard can check it
        global doom_play_area
        doom_play_area = (bx0 - pad + t, bx1 + pad - t,
                          bz0 - pad + t, bz1 + pad - t, by1)
        doom_bounds_boxes.append(Entity(
            parent=parent, model='cube', collider='box', visible=False,
            position=(cx, lid, cz), scale=(w, 1.0, d)))            # the roof

        # SEAL THE DEAD CORRIDORS
        # A solid invisible block filling each blacklisted area, floor to
        # lid, so even if there is some route up there you bump into it
        # instead of getting in. They go in doom_bounds_boxes too, which
        # means the navigation rays already ignore them - so sealing a zone
        # cannot accidentally create new "floor" on top of the seal.
        if DOOM_SEAL_DEAD_ZONES:
            for centre, r in DOOM_DEAD_ZONES:
                doom_bounds_boxes.append(Entity(
                    parent=parent, model='cube', collider='box', visible=False,
                    position=(centre.x, (by1 + lid) / 2, centre.z),
                    scale=(r * 1.6, lid + 24, r * 1.6)))
            print('   %d dead zone(s) sealed off' % len(DOOM_DEAD_ZONES))

        # THE SKY OVER DOOM
        # DOOM's F_SKY1 flats are hidden (DOOM_HIDE_SKY_FLATS), which means
        # the outdoor bits of E1M1 open onto nothing at all. This puts my
        # grid-of-death picture up there instead.
        #
        # It is a sphere INSIDE the boundary box rather than a Sky() prefab,
        # for two reasons: it has to switch off with doom_root like
        # everything else in this scene, and it has to be fog-proof and unlit
        # so it reads as a backdrop rather than a wall you might try to walk
        # to.
        if DOOM_SKY_TEXTURE:
            stex = crunchy_texture(None, DOOM_SKY_TEXTURE, detail=FULL_DETAIL)
            if stex is None:
                print('!! %s not found - DOOM keeps its empty sky'
                      % DOOM_SKY_TEXTURE)
            else:
                sky = Entity(parent=parent, model='sphere',
                             position=(cx, by1 * 0.5, cz),
                             scale=max(w, d) * DOOM_SKY_SCALE,
                             texture=stex, double_sided=True, unlit=True,
                             color=color.white)
                try:
                    sky.setFogOff(1)
                except Exception:
                    pass
                print('   DOOM sky: %s' % DOOM_SKY_TEXTURE)
        print(f'DOOM bounds: box {w:.0f} x {lid:.0f} x {d:.0f} around the level '
              f'({len(doom_bounds_boxes)} pieces, all excluded from navigation)')

    print(f'DOOM map: {len(pieces)} textured pieces, {len(every_vertex) // 3} triangles')
    return collision, pieces


# ==================================================================
# PLAYER MOVEMENT - walking, jumping, crouching
# ==================================================================
player = FirstPersonController(
    position=OFFICE_SPAWN,
    speed=OFFICE_SPEED,
)
player.collider = BoxCollider(player, Vec3(0, PLAYER_HEIGHT / 2, 0),
                              Vec3(0.8, PLAYER_HEIGHT, 0.8))
player.visible_self = True
player.gravity = 1               # was 0, which meant you floated. 1 = you walk.

# do not change any of the features in the game."
# Nothing below changes a single thing you can see. It changes how many
_ppos_frame = -1
_ppos = Vec3(0, 0, 0)
_frame_id = [0]


def player_pos():
    global _ppos_frame, _ppos
    if _frame_id[0] != _ppos_frame:
        _ppos_frame = _frame_id[0]
        _ppos = Vec3(player.world_position)
    return _ppos


class FrameTicker(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)

    def update(self):
        _frame_id[0] += 1


frame_ticker = FrameTicker()
player.mouse_sensitivity = MOUSE_SENS

# FirstPersonController builds its camera pivot at height 2 before it reads any
# keyword arguments, so shortening the player takes these two lines rather than
# one. Nothing inside the controller is edited.
player.height = PLAYER_HEIGHT
player.camera_pivot.y = PLAYER_HEIGHT
player.health = PLAYER_MAX_HP
# GAMEPLAY_FOV, not a loose 95, so the dialogue camera and this line can
# never disagree about what "normal" is. Changing your field of view is now
# one number in SECTION 1 and it is correct everywhere.
camera.fov = GAMEPLAY_FOV

editor_camera = EditorCamera(enabled=False, ignore_paused=True)


def pause_input(key):
    # TAB IS DEVELOPER ONLY, AND IT IS THE IMPORTANT ONE
    # This detaches the camera from the player AND pauses the game. A player
    # who hits TAB - which people do, reflexively, looking for an inventory -
    # is left floating outside their own body with no idea what happened and
    # no obvious way back. Of everything behind DEV_MODE this is the one that
    # would have read as the game being broken.
    if DEV_MODE and key == 'tab':    # toggle edit/play mode
        editor_camera.enabled = not editor_camera.enabled
        player.cursor.enabled = not editor_camera.enabled
        mouse.locked = not editor_camera.enabled
        editor_camera.position = player.position
        application.paused = editor_camera.enabled
        if hands_rig:                # no floating hands in the editor view
            hands_rig.enabled = not editor_camera.enabled


def _esc_input(key):
    if key != 'escape':
        return
    if _menu_open:
        return
    # ---- ESC BACKS OUT OF A CONVERSATION FIRST ----
    # I wanted New Vegas behaviour and this is the half of it people
    # forget: Esc leaves the conversation, it does not pause the game. Only
    # once you are out of the conversation does Esc go back to being pause.
    if dialogue_cam_on:
        talk_box.close()
        return
    set_paused_menu(not _paused_menu)


pause_handler = Entity(ignore_paused=True, input=pause_input)
esc_handler = Entity(ignore_paused=True, input=_esc_input)


def step_assist():
    if not player.enabled or not player.grounded:
        return
    direction = getattr(player, 'direction', None)
    if direction is None or not direction.length():
        return

    # is something right in front of my feet?
    blocked = raycast(player.world_position + Vec3(0, 0.25, 0), direction,
                      distance=0.7, ignore=(player,))
    if not blocked.hit:
        return

    # is there floor just past it, no more than STEP_HEIGHT up?
    probe_from = player.world_position + direction * 0.7 + Vec3(0, STEP_HEIGHT + 0.5, 0)
    ground = raycast(probe_from, Vec3(0, -1, 0), distance=STEP_HEIGHT + 0.6, ignore=(player,))
    if not ground.hit:
        return

    rise = ground.world_point.y - player.world_y
    if rise <= 0.05 or rise > STEP_HEIGHT:
        return


    # is there headroom up there? don't shove the player into a ceiling
    headroom = raycast(ground.world_point + Vec3(0, 0.1, 0), Vec3(0, 1, 0),
                       distance=player.height, ignore=(player,))
    if headroom.hit:
        return

    player.y = ground.world_point.y + 0.02


# ==================================================================
# PLAYER BODY - the visible legs and chest
# ==================================================================
def build_body():
    # indexed lookup, not a fresh walk of the project - see gun_mesh()
    obj = find_asset(f'{BODY_MODEL}.obj')
    if obj is None:
        print(f'!! could not find {BODY_MODEL}.obj anywhere in the project')
        return None

    def drop(a, b, c):
        if BODY_CUT_ARMS and all(abs(p[0]) > BODY_ARM_CUT_X
                                 and p[1] > BODY_ARM_CUT_Y for p in (a, b, c)):
            return True
        if BODY_CUT_HEAD and all(p[1] > BODY_CUT_TOP_Y for p in (a, b, c)):
            return True
        return False

    # flip_x is OFF here so the winding order survives and backface culling
    # works. That culling is what hides the inside of the head you're sitting
    # in: a closed mesh viewed from inside shows nothing at all.
    groups = load_obj_by_material(obj, scale=BODY_SCALE, drop_triangle=drop,
                                  flip_x=False, shade=True)

    # THE ANCHOR AND THE VISIBLE BODY ARE TWO THINGS NOW
    # anchor  : invisible, parented to you, moves and rocks exactly as the
    #           body always did. BodyGait animates THIS, unchanged.
    # visual  : the actual mesh, living on the viewmodel render pass so
    #           nothing in the world can draw in front of it.
    # Every frame BodyViewmodelFollower copies the anchor's position relative
    # to the camera onto the visual. build_body() returns the anchor, so
    # `player_body` still means what it always meant and every other line in
    # the file that touches it keeps working.
    #
    # ---- THIS LINE WAS COMMENTED OUT AND IT IS WHY THE GAME WOULD NOT
    #      START ----
    # The next line had been turned into a comment, along with four of the
    # comment lines around it - each one gaining a SECOND '#', which is what
    # an editor does when you press "comment out" on a block that is already
    # part comment. So `anchor` never got created, and the very next line
    # asked for it: NameError: name 'anchor' is not defined. A horrible one
    # to find, because the file looked completely normal.
    anchor = Entity(parent=player, position=BODY_OFFSET, enabled=SHOW_BODY)

    # The viewmodel render pass does not exist yet at this point in the file -
    # it gets built about a hundred lines further down, with the hands. So the
    # mesh starts as an ordinary child of the anchor and gets MOVED onto the
    # layer by attach_body_to_viewmodel() once the layer is up. Building it
    # here and adopting it later was much less disruptive than moving the
    # whole body section below the hands.
    visual = Entity(parent=anchor, enabled=SHOW_BODY)
    on_layer = False

    tris = 0
    for material, (vlist, ulist, clist) in groups.items():
        if not vlist:
            continue
        tris += len(vlist) // 3
        tex = crunchy_texture(None, BODY_TEXTURE) if BODY_TEXTURE else None
        Entity(parent=visual,
               model=Mesh(vertices=vlist, uvs=ulist, colors=clist,
                          mode='triangle', static=True),
               texture=tex,
               color=color.white if tex else BODY_COLOR,
               double_sided=BODY_DOUBLE_SIDED, unlit=True)

    anchor.visual = visual
    anchor.on_layer = on_layer
    cuts = []
    if BODY_CUT_ARMS:
        cuts.append('arms')
    if BODY_CUT_HEAD:
        cuts.append('head above %.1f' % BODY_CUT_TOP_Y)
    print('body: %d triangles%s, %s'
          % (tris, (' (' + ' + '.join(cuts) + ' removed)') if cuts else '',
             'double-sided' if BODY_DOUBLE_SIDED else 'single-sided'))
    return anchor


player_body = build_body()


class BodyViewmodelFollower(Entity):
    def update(self):
        if player_body is None or not getattr(player_body, 'on_layer', False):
            return
        visual = player_body.visual
        visual.enabled = player_body.enabled and not _menu_open
        if not visual.enabled:
            return
        try:
            visual.set_transform(player_body.get_transform(camera))
        except Exception as e:
            print('!! body follower failed, dropping back to the world:', e)
            player_body.on_layer = False
            visual.reparent_to(player_body)
            visual.set_transform(render.get_transform(render))


body_viewmodel_follower = BodyViewmodelFollower()


class BodyGait(Entity):
    def update(self):
        if player_body is None or _menu_open or application.paused:
            return
        t = movement.bob_t          # the shared step clock (MovementController)
        moving = (getattr(player, 'direction', Vec3(0, 0, 0)).length() > 0
                  and getattr(player, 'grounded', True) and player.enabled)

        if moving:
            rock  = math.sin(t) * BODY_WALK_ROCK          # weight left/right
            twist = math.sin(t * 0.5) * BODY_WALK_TWIST   # hips, half tempo
            dip   = -abs(math.sin(t)) * BODY_WALK_DIP     # sink on footfall
            lead  = -BODY_WALK_LEAD                       # lean into the walk
        else:
            # idle: a slow breathe so the body never looks parked
            rock  = math.sin(time.time() * 1.1) * 0.6
            twist = 0.0
            dip   = math.sin(time.time() * 1.6) * 0.008
            lead  = 0.0

        k = min(1, time.dt * 10)
        player_body.rotation_z = lerp(player_body.rotation_z, rock, k)
        player_body.rotation_y = lerp(player_body.rotation_y, twist, k)
        player_body.y = lerp(player_body.y, BODY_OFFSET.y + dip, k)
        player_body.z = lerp(player_body.z, BODY_OFFSET.z + lead, k)


body_gait = BodyGait()


# ==================================================================
# FIRST PERSON HANDS
# ==================================================================
# HALF-LIFE 2 ARMS. The damaged-hands model is still here as the other
# option - its folder goes next to launcher.py with the .obj and both .png files
# inside it. Set HANDS_USE_HL2 = False and you are straight back on it;
# both are still wired up and i deleted nothing.
def make_viewmodel_layer():
    if not HANDS_OWN_DEPTH_LAYER:
        return None, None
    try:
        from panda3d.core import NodePath as PandaNodePath, PerspectiveLens, Camera as PandaCamera

        lens = PerspectiveLens()
        lens.set_fov(camera.fov)
        lens.set_aspect_ratio(window.aspect_ratio)
        lens.set_near_far(0.01, 50)

        cam_node = PandaCamera('viewmodel_cam')
        cam_node.set_lens(lens)

        root = PandaNodePath('viewmodel_render')
        cam_np = root.attach_new_node(cam_node)

        region = application.base.win.make_display_region(0, 1, 0, 1)
        region.set_sort(10)
        region.set_clear_depth_active(True)     # <- the important line
        region.set_clear_depth(1.0)
        region.set_clear_color_active(False)    # keep what the world drew
        region.set_camera(cam_np)
        return root, lens
    except Exception as e:
        print('viewmodel layer unavailable, falling back to normal camera:', e)
        return None, None


viewmodel_root, viewmodel_lens = make_viewmodel_layer()


def attach_body_to_viewmodel():
    if not BODY_ON_VIEWMODEL or player_body is None:
        return
    if viewmodel_root is None:
        print('body: no viewmodel pass, so the body stays in the world and '
              'walls can still cut into it')
        return
    player_body.visual.reparent_to(viewmodel_root)
    player_body.on_layer = True
    print('body: moved onto the viewmodel pass - nothing in the world can '
          'draw in front of it now')


attach_body_to_viewmodel()
if viewmodel_root is None:
    # worth shouting about. With this layer working the hands live in their
    # own scene graph with their own camera, drawn after the world - so
    # nothing in the world can reach them, which is the architectural reason
    # they cannot be fogged or tinted. WITHOUT it they are ordinary children
    # of the camera, in the world, and every transparent thing in the scene
    # gets drawn on top of them. If the hand colour problem ever comes back,
    # THIS LINE IS THE FIRST THING TO CHECK.
    print('\n!! THE HANDS ARE NOT ON THEIR OWN RENDER LAYER.')
    print('!! They are children of the camera instead, which means world '
          'geometry can draw over them and tint them.')
    print('!! If your hands change colour again, this is why - tell me and I '
          'will special-case it.\n')
else:
    print('hands: own render layer active - world fog and transparency cannot '
          'reach them')


# The parsed hand geometry, kept so it can be built more than once. A Panda3D
# node can only have ONE parent, so the arms in front of your face and the
# arms wrapped around a gun cannot be the same entity - each one needs its
# own Mesh built from the same vertex data. Learned that the hard way.
_hand_parts = []        # [(vertices, uvs, colors, texture), ...]


def hand_entity(parent, tint=None):
    holder = Entity(parent=parent)
    for hv, hu, hc, tex in _hand_parts:
        Entity(parent=holder,
               model=Mesh(vertices=list(hv), uvs=list(hu), colors=list(hc),
                          mode='triangle', static=True),
               texture=tex,
               color=tint or (color.white if tex else RGB(214, 178, 156)),
               double_sided=True, unlit=True)
    return holder


def build_hands():
    folder = ASSETS / HANDS_FOLDER
    obj = folder / HANDS_OBJ
    if not obj.exists():
        # indexed lookup, not a fresh walk of the project - see gun_mesh()
        found = find_asset(HANDS_OBJ)
        if found is None:
            print(f'!! could not find {HANDS_OBJ}. Put the "{HANDS_FOLDER}" folder next to launcher.py')
            return None, None
        obj, folder = found, found.parent

    groups = load_obj_by_material(obj, scale=HANDS_SCALE,
                                  flip_x=HANDS_MIRROR, shade=True)

    rig = Entity(parent=viewmodel_root if viewmodel_root else camera)
    model_root = Entity(parent=rig, position=HANDS_POS, rotation=HANDS_ROT)
    # The HL2 arms are a single mesh with both arms already posed, so there's
    # nothing to split - splitting it down x=0 would saw it in half.
    single = HANDS_SPREAD <= 0.0001
    side_root = {0: model_root} if single else {
        -1: Entity(parent=model_root, position=(-HANDS_SPREAD, 0, 0)),
        +1: Entity(parent=model_root, position=(HANDS_SPREAD, 0, 0)),
    }

    tris = 0
    for material, (vlist, ulist, clist) in groups.items():
        if not vlist:
            continue
        tris += len(vlist) // 3
        # full.obj has no .mtl, so match "defaultMat.001" -> "defaultMat" etc.
        prefix = material.split('.')[0]
        tex_name = HAND_MATERIAL_TEXTURES.get(prefix)
        if HANDS_USE_BODY_TEXTURE and BODY_TEXTURE:
            # Same image as the body, so the arms and the torso you see when
            # you look down are made of the same stuff. Searched project-wide
            # rather than in the hands folder, because that's where it lives.
            tex = crunchy_texture(None, BODY_TEXTURE)
        else:
            tex = crunchy_texture(folder, tex_name) if tex_name else None

        halves = {0: ([], [], [])} if single else {-1: ([], [], []), +1: ([], [], [])}
        for t in range(0, len(vlist), 3):
            tri = [vlist[t], vlist[t + 1], vlist[t + 2]]
            uv = [ulist[t], ulist[t + 1], ulist[t + 2]]
            col = [clist[t], clist[t + 1], clist[t + 2]] if clist else None

            # which hand is this triangle part of, in the original mesh?
            if single:
                side = 0
            else:
                mid_x = (tri[0][0] + tri[1][0] + tri[2][0]) / 3
                side = -1 if mid_x < 0 else 1

            hv, hu, hc = halves[side]
            hv.extend(tri)
            hu.extend(uv)
            if col:
                hc.extend(col)

        for side, (hv, hu, hc) in halves.items():
            if not hv:
                continue
            _hand_parts.append((hv, hu, hc, tex))   # so gun hands can reuse it
            Entity(parent=side_root[side],
                   model=Mesh(vertices=hv, uvs=hu, colors=hc,
                              mode='triangle', static=True),
                   texture=tex,
                   color=color.white if tex else RGB(214, 178, 156),
                   double_sided=True, unlit=True)

    print(f'hands: {tris} triangles'
          + ('  (HL2 arms, single mesh)' if single else ', split into left and right'))
    return rig, model_root


hands_rig, hands_model = build_hands()

# ==================================================================
# GUN_HANDS_SCALE was 0.030, so 2.553 x 0.030 = 7.7 CENTIMETRES
# ==================================================================
GUN_HANDS_ON = False
GUN_HANDS_SCALE = 0.10


def build_gun_hands():
    if not _hand_parts or not GUN_HANDS_ON:
        return None
    rig = Entity(parent=viewmodel_root if viewmodel_root else camera,
                 enabled=True)
    hand_entity(rig)
    rig.scale = GUN_HANDS_SCALE
    return rig


gun_hands = build_gun_hands()

# ==================================================================
# WHERE THE HANDS GO, DERIVED FROM THE GUN ITSELF
# ==================================================================
# The old table put them at y = -0.70 to -0.80 while the guns sit at y = -0.10
# to -0.17 - more than half a metre BELOW the weapon, off the bottom of the
# screen. Six hand-typed rows, all six wrong in the same direction.
#
# So they are not typed in any more. The grip is the WEAPON'S OWN position
# plus one shared offset, which means:
#   - it can never be half a metre away from the gun again
#   - retuning a weapon's pos in the WEAPONS table moves its hands with it
#   - there is one offset to nudge instead of six rows to keep in step
#
# THE OFFSET, and what each number does:
#   y  -0.085   just below the gun's centre line, so the hands come up
#               underneath it the way a hand actually meets a grip
#   z  +0.045   slightly FURTHER from your eye than the gun. This is what
#               makes the gun sit in front of the hands rather than inside
#               them - together with the render order forced in
#               pose_gun_hands, the gun always wins.
#   x   0.0     dead on the gun. The weapons are already offset to the right.
# ===================== MOVING THEM YOURSELF ==================
# The first way did not really work, so there are now TWO ways to shift
# them about, and the second one is the one to use.
#
# BY HAND: change the three numbers below. That is the whole control.
#     x   negative = left across the screen, positive = right
#     y   negative = DOWN. This is the one to try first if you cannot see
#         them at all - they were half a metre too low before.
#     z   bigger = further away from your eye. Also makes them look SMALLER,
#         because that is how perspective works, so z is your size control
#         as much as GUN_HANDS_SCALE is.
# and GUN_HANDS_SCALE, a few lines up, for how big they are.
#
# IN THE GAME, which is much faster: press G to turn the nudge keys on, then
#     I / K    up and down
#     J / L    left and right
#     U / O    nearer and further
#     Y / H    bigger and smaller
#     N / M    rotate the wrists
#     P        print the numbers you have arrived at
# It prints a line you can paste straight over the three below, so you can
# stand there with a gun out, move them until they look right, press P, and
# copy the answer in. Nothing is saved automatically - P is how you keep it.
WEAPON_GRIP_OFFSET = Vec3(0.0, -0.085, 0.045)
# 280 on X is the same angle as the main viewmodel's HANDS_ROT, which i tuned
# by hand and which is known to point the forearms forward properly. Reusing
# it means the arms come at the gun from below and behind, like real hands do,
# instead of from somewhere completely different - the old table used 218-224,
# which is where the arms-at-the-bottom-of-the-screen problem came from.
WEAPON_GRIP_ROT = Vec3(280, 0, 0)

# PER-WEAPON OVERRIDES, if one of them ends up looking wrong. Empty on
# purpose: anything in here replaces the derived value for that gun only, and
# takes (position, rotation) exactly as the old table did.
WEAPON_GRIP = {
    # 'minigun': (Vec3(0.23, -0.20, 0.66), Vec3(280, 0, 0)),
}


def pose_gun_hands(spec):
    if gun_hands is None:
        return
    if spec is None:
        gun_hands.enabled = False
        return
    override = WEAPON_GRIP.get(spec['key'])
    if override is not None:
        pos, rot = override
    else:
        base = spec['pos']
        pos = Vec3(base.x + WEAPON_GRIP_OFFSET.x,
                   base.y + WEAPON_GRIP_OFFSET.y,
                   base.z + WEAPON_GRIP_OFFSET.z)
        rot = WEAPON_GRIP_ROT
    gun_hands.position = pos
    gun_hands.rotation = rot
    gun_hands.enabled = True
    # the gun in front, the hands behind, guaranteed
    try:
        gun_hands.setBin('fixed', 50)
        gun_hands.setDepthWrite(False)
        gun = weapons.by_key.get(spec['key']) if weapons else None
        if gun is not None:
            gun.setBin('fixed', 60)
            gun.setDepthWrite(True)
    except Exception as exc:
        print('!! could not force the gun in front of the hands (%s) - they '
              'may interpenetrate' % exc)


def build_held_phone():
    if hands_model is None:
        return None
    holder = Entity(parent=hands_model, position=PHONE_HELD_POS,
                    rotation=PHONE_HELD_ROT, scale=PHONE_HELD_SCALE,
                    enabled=False)
    tex = crunchy_texture(None, PHONE_TEXTURE)
    # A BIG FLAT PNG OF A PHONE, held up like a slab. Deliberately silly and
    # deliberately readable - the whole point is that you can actually see
    # store_control, so it is one large quad facing you rather than a cube
    # whose texture you only ever catch at an angle. double_sided so it is
    # there whichever way it ends up turned.
    body = Entity(parent=holder, model='quad', scale=(1.6, 2.4, 1),
                  texture=tex, color=color.white if tex else RGB(35, 33, 38),
                  unlit=True, double_sided=True)
    # a thin edge behind it so it isn't paper-thin from the side
    Entity(parent=body, model='cube', z=0.06, scale=(1.0, 1.0, 0.04),
           color=RGB(30, 28, 33), unlit=True)
    return holder


held_phone = build_held_phone()


# ==================================================================
# NOTHING YOU ARE HOLDING EVER GETS FOGGED
# ==================================================================
# ----------------------------------------------------------------------
# THIS IS THE FIX FOR "the fog textures start affecting my hands and they
# take the colour of the sky", and for the hands going black in the office.
#
# Panda3D fog is a render attribute that flows DOWN the node graph, and it is
# inherited by every child unless a node explicitly opts out. The viewmodel
# lives on its own display region, which sorts it in front of the world - but
# sorting has nothing to do with fog, so the arms were still inheriting it and
# getting tinted by whatever the sky was doing that second.
#
# setFogOff(1) is the opt-out. The 1 is a priority, and it beats the fog being
# set further up. Called on every single thing you hold or wear - the arms,
# the arms wrapped round a gun, all six weapon models, the handset, your own
# body, and the whole 2D UI - so none of them can ever be touched by weather
# again, in any scene, whatever the fog is doing.
#
# If you ever add another viewmodel object, add it to this list.
# ######################################################################
def make_fog_proof(*things):
    done = 0
    for t in things:
        if t is None:
            continue
        try:
            t.setFogOff(1)
            done += 1
        except Exception as e:
            print('!! could not make something fog-proof:', e)
    return done


# The arms, the phone and your body exist now, so they can be done here. The
# guns and the fallback sprite are built much further down, so they get done
# at the end of the weapon section - look for make_fog_proof again there.
make_fog_proof(hands_rig, hands_model, gun_hands, held_phone, player_body,
               getattr(player_body, 'visual', None),
               camera.ui, viewmodel_root)


AD_BIN = 'fixed'
AD_BIN_ORDER = 400        # picture. The X sits at +1 and +2 above this.


def ad_layer(entity, order):
    try:
        entity.setBin(AD_BIN, order)
        entity.setDepthTest(False)
        entity.setDepthWrite(False)
    except Exception as exc:
        print('!! could not force the advert draw order (%s) - they may be '
              'covered by other things' % exc)
    make_fog_proof(entity)
    return entity


class HandAnimator(Entity):
    def __init__(self):
        super().__init__()
        self.bob_t = 0.0
        self.offset = Vec3(0, 0, 0)      # smoothed, so nothing snaps
        self.sway = Vec2(0, 0)

    def update(self):
        if not hands_rig or _menu_open or application.paused:
            return

        # keep the viewmodel lens matched to the window if it gets resized
        if viewmodel_lens:
            viewmodel_lens.set_aspect_ratio(window.aspect_ratio)
            viewmodel_lens.set_fov(camera.fov)

        # dead still outside the levels - see HANDS_MOTION_IN
        if game is not None and game.state not in HANDS_MOTION_IN:
            hands_rig.position = lerp(hands_rig.position, Vec3(0, 0, 0),
                                      min(1, time.dt * 8))
            hands_rig.rotation = lerp(hands_rig.rotation, Vec3(0, 0, 0),
                                      min(1, time.dt * 8))
            hands_rig.scale = lerp(hands_rig.scale, Vec3(1, 1, 1),
                                   min(1, time.dt * 8))
            return

        moving = (getattr(player, 'direction', Vec3(0, 0, 0)).length() > 0
                  and player.grounded and player.enabled)

        if moving:
            self.bob_t += time.dt * HANDS_BOB_SPEED
            # a horizontal figure-eight: side to side at half the rate of the
            # up and down, which is what makes it read as footsteps
            target = Vec3(math.sin(self.bob_t) * HANDS_BOB_AMOUNT,
                          -abs(math.sin(self.bob_t * 2)) * HANDS_BOB_AMOUNT,
                          0)
            # THE SCALE IS DRIVEN BY THE SAME CLOCK AS THE BOB. Same bob_t,
            # same rhythm - the hands swell on the footfall and shrink on the
            # lift, so the scaling IS the bopping rather than a separate
            # effect drifting out of sync with it. HANDS_SCALE_PULSE is the
            # dial.
            pulse = 1.0 + math.sin(self.bob_t * 2) * HANDS_SCALE_PULSE
            # AND THEY ROCK, not just slide. Same clock again, so the
            # roll peaks as the weight lands. This is the part that actually
            # reads as "the hands are attached to a body that is walking".
            step_rot = Vec3(-abs(math.sin(self.bob_t * 2)) * HANDS_BOB_PITCH,
                            math.sin(self.bob_t) * HANDS_BOB_YAW,
                            math.sin(self.bob_t) * HANDS_BOB_ROLL)
        else:
            breathe = math.sin(time.time() * 1.6) * HANDS_BREATHE
            target = Vec3(0, breathe, 0)
            # standing still: a slow breathing pulse instead of the step pulse
            pulse = 1.0 + math.sin(time.time() * 1.6) * HANDS_SCALE_PULSE * 0.3
            # a tiny idle drift, so they are never completely dead
            step_rot = Vec3(math.sin(time.time() * 1.1) * HANDS_BOB_PITCH * 0.25,
                            math.sin(time.time() * 0.8) * HANDS_BOB_YAW * 0.25,
                            math.sin(time.time() * 0.9) * HANDS_BOB_ROLL * 0.25)

        self.offset = lerp(self.offset, target, min(1, time.dt * 10))
        self.step_rot = lerp(getattr(self, 'step_rot', Vec3(0, 0, 0)), step_rot,
                             min(1, time.dt * 10))

        # hands lag behind the camera when you whip the mouse around
        self.sway = lerp(self.sway,
                         Vec2(-mouse.velocity[0] * HANDS_SWAY,
                              -mouse.velocity[1] * HANDS_SWAY),
                         min(1, time.dt * 8))

        hands_rig.position = self.offset + Vec3(self.sway.x, self.sway.y, 0)
        # the mouse sway and the walk rock ADD, so turning while walking moves
        # them more than either does alone - which is the "shift around when I
        # move" i was after
        hands_rig.rotation = Vec3(
            -self.sway.y * 40 + self.step_rot.x,
            self.sway.x * 40 + self.step_rot.y,
            self.sway.x * 25 + self.step_rot.z)
        hands_rig.scale = lerp(hands_rig.scale, Vec3(pulse, pulse, pulse),
                               min(1, time.dt * 12))


hand_animator = HandAnimator()


# ==================================================================
# WEAPONS - the guns and shooting
# ==================================================================
# find_folder(), not ASSETS / WEAPON_FOLDER. The direct join only works if the
# weapons folder sits right next to launcher.py, which stopped being true the moment
# i tidied everything into media/. find_folder() tries that spot first and then
# looks it up in the index, so the folder can live anywhere in the project.
WEAPON_ASSETS = find_folder(WEAPON_FOLDER) or (ASSETS / WEAPON_FOLDER)
_gun_sounds = {}
_gun_mesh_data = {}


def gun_visual(spec):
    if spec.get('glb'):
        return dict(model=spec['model'])
    return dict(model=gun_mesh(spec['model']),
                texture=crunchy_texture(WEAPON_ASSETS, WEAPON_TEXTURE))


def gun_mesh(name):
    if name not in _gun_mesh_data:
        # THIS LINE USED TO BE THE SLOWEST THING IN THE GAME
        # It was `for candidate in ASSETS.rglob(f'{name}.obj')` - a FRESH
        # recursive walk of the entire project, per gun. Seven guns, seven
        # walks of 21,890 files, every launch, before the title screen.
        #
        # I found it by dumping the stack while the game was still loading:
        # it was sitting in pathlib.stat inside rglob, called from right
        # here. Not guessed - caught in the act.
        #
        # find_asset() answers from an index built by ONE walk, and that
        # walk skips build/ and .venv/. Same answer, none of the cost.
        path = find_asset(f'{name}.obj')
        if path is None:
            print(f'!! could not find {name}.obj - is the "{WEAPON_FOLDER}" folder in the project?')
            _gun_mesh_data[name] = None
        else:
            groups = load_obj_by_material(path, flip_x=False, shade=True)
            verts, uvs, cols = [], [], []
            for vlist, ulist, clist in groups.values():   # all share level.png
                verts += vlist
                uvs += ulist
                cols += clist
            _gun_mesh_data[name] = (verts, uvs, cols)

    data = _gun_mesh_data[name]
    if not data:
        return 'cube'
    verts, uvs, cols = data
    return Mesh(vertices=list(verts), uvs=list(uvs), colors=list(cols),
                mode='triangle', static=True)

# Declared up front because the weapons and pickups ask what state the game is
# in, and they get built before the state machine does.
game = None
weapons = None
doom_music = None


def gun_sound(name):
    if name not in _gun_sounds:
        _gun_sounds[name] = safe_audio(name, autoplay=False, loop=False)
    return _gun_sounds[name]


# ==================================================================
# WHAT THIS USED TO BE. Thirty filenames - DSPOSIT1, DSSGTDTH, DSPISTOL
# ==================================================================
DOOM_SOUNDS = {}
_doom_sounds = {}


def doom_sound(kind):
    if kind in _doom_sounds:
        return _doom_sounds[kind]
    clip = None
    for name in DOOM_SOUNDS.get(kind, []):
        clip = safe_audio(name, autoplay=False, loop=False)
        if clip:
            break
    _doom_sounds[kind] = clip
    return clip


class Bullet(Entity):
    def __init__(self, start, direction, speed=90, life=1.2):
        super().__init__(
            parent=doom_root,
            model=gun_mesh('bullet'),
            texture=crunchy_texture(WEAPON_ASSETS, WEAPON_TEXTURE),
            scale=0.055,
            position=start,
            unlit=True,
        )
        self.look_at(start + direction)
        self.direction = direction
        self.speed = speed
        self.life = life

    def update(self):
        self.position += self.direction * self.speed * time.dt
        self.life -= time.dt
        if self.life <= 0:
            destroy(self)


class Rocket(Entity):
    def __init__(self, start, direction, damage):
        super().__init__(
            parent=doom_root,
            model=gun_mesh('rocket'),
            texture=crunchy_texture(WEAPON_ASSETS, WEAPON_TEXTURE),
            scale=0.10,
            position=start,
            unlit=True,
        )
        self.look_at(start + direction)
        self.direction = direction
        self.damage = damage
        self.life = 5

    def explode(self):
        for radius, col, delay in ((1.0, RGB(255, 240, 180), 0.0),
                                   (2.6, RGB(255, 150, 40), 0.03),
                                   (4.0, RGB(120, 90, 70), 0.08)):
            puff = Entity(parent=doom_root, model='sphere', position=self.world_position,
                          scale=radius * 0.4, color=col, unlit=True)
            puff.animate_scale(radius * 2, duration=0.35, delay=delay)
            puff.animate('alpha', 0, duration=0.35, delay=delay)
            destroy(puff, delay=0.5)

        for enemy in list(game.enemies):
            gap = distance(enemy.world_position, self.world_position)
            if gap < ROCKET_SPLASH:
                enemy.take_damage(self.damage * PLAYER_DAMAGE_MULT
                                  * (1 - gap / ROCKET_SPLASH))
                hitmarker.hit(kill=getattr(enemy, 'dying', False))

        # rockets hurt you too, which is what stops it being the answer to
        # everything in a corridor
        gap = distance(player.world_position + Vec3(0, 1, 0), self.world_position)
        if gap < ROCKET_SPLASH:
            hurt_player(22 * (1 - gap / ROCKET_SPLASH))

        beep(pitch=-30, length=0.5, wave='noise', volume=0.7)
        # an explosion is heard a long way further than a rifle
        alert_enemies_near(self.world_position, ENEMY_SHOT_HEARD * 1.6)
        destroy(self)

    def update(self):
        move = self.direction * 26 * time.dt
        hit = raycast(self.world_position, self.direction,
                      distance=move.length() + 0.5, ignore=(self, player))
        if hit.hit:
            if getattr(hit.entity, 'is_enemy', False):
                hit.entity.take_damage(self.damage * PLAYER_DAMAGE_MULT)
                hitmarker.hit(kill=getattr(hit.entity, 'dying', False))
            self.explode()
            return
        for enemy in game.enemies:
            if distance(enemy.world_position, self.world_position) < 1.4:
                self.explode()
                return
        self.position += move
        self.life -= time.dt
        if self.life <= 0:
            self.explode()


class Weapon(Entity):
    def __init__(self, spec):
        super().__init__(
            parent=viewmodel_root if viewmodel_root else camera,
            **gun_visual(spec),
            scale=spec['scale'],
            position=spec['pos'],
            rotation=spec['rot'],
            unlit=True,
            # SOLID. Without this only the front faces draw, so on any model
            # whose normals point inward you see straight through the shell
            # to the inside of the far side - which is exactly the "it looks
            # like a model, not a gun" problem i had. The 9mm looked right
            # all along because it is a .glb and arrives with its normals
            # already correct.
            double_sided=True,
            enabled=False,
        )
        self.spec = spec
        self.rest_pos = Vec3(spec['pos'])
        self.rest_rot = Vec3(spec['rot'])
        self.cooldown = 0.0
        self.bob_t = 0.0

        # the minigun has a barrel that spins while you hold the trigger
        self.barrel = None
        if spec.get('spin_barrel'):
            self.barrel = Entity(parent=self, model=gun_mesh('minigun-barrel'),
                                 texture=crunchy_texture(WEAPON_ASSETS, WEAPON_TEXTURE),
                                 unlit=True)

    @property
    def muzzle(self):
        return camera.world_position + camera.forward * 0.6 - camera.up * 0.08

    def can_fire(self):
        return self.cooldown <= 0

    def fire(self):
        spec = self.spec
        self.cooldown = spec['cooldown']

        clip = gun_sound(spec['sound'])
        if clip:
            clip.play()
        else:
            shoot_sound()
        # A GUNSHOT IS THE LOUDEST THING IN A DOOM LEVEL. Everything within
        # earshot comes to find out what it was, which is how a firefight in
        # one room pulls the next room in on top of it.
        # Once per TRIGGER PULL, not once per pellet - it walks the whole
        # enemy list, and a shotgun would otherwise do that seven times for
        # one bang.
        if game is not None and game.state == 'doom':
            alert_enemies_near(camera.world_position, ENEMY_SHOT_HEARD)

        if spec.get('rocket'):
            Rocket(self.muzzle, camera.forward, spec['damage'])
        else:
            for _ in range(spec['pellets']):
                spread = spec['spread']
                aim = (camera.forward
                       + camera.right * random.uniform(-spread, spread)
                       + camera.up * random.uniform(-spread, spread)).normalized()
                self.hitscan(aim)
                # ONE ENTITY PER PELLET, and a shotgun has seven of them.
                # See BULLET_TRACERS - this is the slowdown you can feel when
                # you shoot, and switching it off changes nothing at all
                # about what the shot actually does.
                if BULLET_TRACERS:
                    Bullet(self.muzzle, aim)

        # recoil: snap up, settle back
        kick = spec['kick']
        self.rotation_x = self.rest_rot.x - kick
        self.z = self.rest_pos.z - 0.05
        self.animate('rotation_x', self.rest_rot.x, duration=spec['cooldown'] * 0.8,
                     curve=curve.out_quad)
        self.animate('z', self.rest_pos.z, duration=spec['cooldown'] * 0.8,
                     curve=curve.out_quad)
        camera_shake(kick)

    def hitscan(self, aim):
        hit = raycast(camera.world_position, aim, distance=WEAPON_RANGE, ignore=[player])
        if not hit.hit:
            return
        target = hit.entity
        if getattr(target, 'is_enemy', False):
            target.take_damage(self.spec['damage'] * PLAYER_DAMAGE_MULT)
            # asked AFTER the damage, so `dying` is already true if
            # that was the shot that finished it and you get the kill marker
            # on the same frame rather than one late.
            hitmarker.hit(kill=getattr(target, 'dying', False))
        # `target == friend` on its own was too strict. He is a holder entity
        # with a body and six textured meshes hanging off him, so anything
        # that ever gives one of those a collider - now or later - would
        # return the CHILD as the hit and this test would quietly fail with no
        # way to tell from the outside. has_ancestor() accepts a hit anywhere
        # on him, which is what i needed for the shot to register right away.
        elif (game.state == 'finale' and game.finale_choice_ready
              and (target == friend
                   or (target is not None and target.has_ancestor(friend)))):
            game.ending_kill()
        # YOU CAN SHOOT THE PEOPLE NOW
        # Anything with talk_lines is somebody you could have had a
        # conversation with instead. One shot and they are gone for the rest
        # of the run - see kill_npc(). This gets checked AFTER the enemy test
        # so a DOOM enemy is never mistaken for a villager.
        elif VILLAGE_GUN_ON and is_a_person(target):
            kill_npc(target)
            hitmarker.hit(kill=True)
        else:
            spark(hit.world_point)

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= time.dt

        if self.barrel and held_keys['left mouse']:
            self.barrel.rotation_z += 900 * time.dt

        # same walk bob as the hands, just gentler - a gun is heavy
        moving = (getattr(player, 'direction', Vec3(0, 0, 0)).length() > 0
                  and player.grounded and player.enabled)
        if moving:
            self.bob_t += time.dt * HANDS_BOB_SPEED
            target = Vec3(math.sin(self.bob_t) * 0.010,
                          -abs(math.sin(self.bob_t * 2)) * 0.010, 0)
        else:
            target = Vec3(0, math.sin(time.time() * 1.6) * 0.004, 0)

        self.x = lerp(self.x, self.rest_pos.x + target.x - mouse.velocity[0] * 0.35,
                      min(1, time.dt * 9))
        self.y = lerp(self.y, self.rest_pos.y + target.y - mouse.velocity[1] * 0.35,
                      min(1, time.dt * 9))


_shake_amount = 0.0


def camera_shake(amount):
    global _shake_amount
    _shake_amount = max(_shake_amount, amount * 0.018)


# ==================================================================
# THE FIX IS A POOL, WHICH IS WHAT GAMES ACTUALLY DO
# ==================================================================
SPARK_POOL_SIZE = 24
SPARK_LIFE      = 0.10


# A NAME YOU MUST NOT USE ON ANYTHING THAT INHERITS FROM Entity
# This class stores how much life each spark has got left. The obvious name
# for that list is self.left - and self.left is exactly what crashed the game
# on startup:
#
#     AttributeError: property 'left' of 'SparkPool' object has no setter
#
# ursina's Entity already owns .left. It is a READ-ONLY property that hands
# you a direction vector - the way the entity is facing, turned ninety
# degrees. Look in ursina/entity.py around line 647 and you will see it
# declared with @property and no matching @left.setter. A property without a
# setter cannot be assigned to, so the moment __init__ ran, Python refused.
#
# The whole read-only set, for anything that subclasses Entity:
#
#     forward   back   left   right   up   down      direction vectors
#     X   Y   Z                                      integer shortcuts
#     bounds   model_bounds   screen_position
#     types   attributes   loose_children
#
# Never assign to any of those on an Entity subclass. Names like .position,
# .scale, .rotation and .color are all fine - they have setters and are meant
# to be written to.
#
# So the list is called life_left. It reads better anyway.
class SparkPool(Entity):
    def __init__(self):
        super().__init__()
        self.dots = []
        self.life_left = []        # NOT self.left - see the note above
        self.next_one = 0
        self.built = False

    def build(self):
        for _ in range(SPARK_POOL_SIZE):
            dot = Entity(parent=doom_root, model='quad', scale=0.09,
                         color=RGB(255, 230, 150, 200), unlit=True,
                         billboard=True, enabled=False)
            dot.ignore = True          # it must not cost a frame either
            self.dots.append(dot)
            self.life_left.append(0.0)
        self.built = True

    def pop(self, point):
        if not self.built:
            self.build()
        i = self.next_one
        self.next_one = (self.next_one + 1) % len(self.dots)
        dot = self.dots[i]
        dot.position = point
        dot.scale = 0.09
        dot.enabled = True
        self.life_left[i] = SPARK_LIFE

    def update(self):
        if not self.built:
            return
        for i, dot in enumerate(self.dots):
            if self.life_left[i] <= 0:
                continue
            self.life_left[i] -= time.dt
            if self.life_left[i] <= 0:
                dot.enabled = False
            else:
                # shrink as it dies, the same as the animation used to
                dot.scale = 0.09 * (self.life_left[i] / SPARK_LIFE)


spark_pool = SparkPool()


def spark(point):
    if not BULLET_SPARKS:
        return
    spark_pool.pop(point)


class WeaponPickup(Entity):
    def __init__(self, spec, position):
        super().__init__(
            parent=doom_root,
            **gun_visual(spec),
            # A GUN MAY CARRY ITS OWN pickup_scale. Without one the old rule
            # applies - and that rule (0.32 for any .glb) is what turned a
            # 767-unit water gun into a 245-unit one hanging in the sky. Any
            # model that is not authored at roughly real size needs this set:
            # measure it and divide, do not guess. I guessed, once.
            scale=spec.get('pickup_scale',
                           PICKUP_SCALE * (3.2 if spec.get('glb') else 1.0)),
            position=position + Vec3(0, 0.55, 0),
            unlit=True,
        )
        self.spec = spec
        self.base_y = self.y
        self.glow = Entity(parent=doom_root, scale=0.001, visible=False)
        self.label = Text(spec['name'], parent=doom_root, billboard=True, scale=8,
                          position=position + Vec3(0, 1.4, 0), color=RGB(150, 225, 255))

    def update(self):
        if game.state != 'doom':
            return
        self.rotation_y += PICKUP_SPIN * time.dt
        self.y = self.base_y + math.sin(time.time() * 2) * 0.08
        if distance(player_pos(), self.world_position) < PICKUP_RADIUS:
            weapons.unlock(self.spec['key'], announce=True)
            # Take ourselves OUT of the list before dying. Without this the
            # reference stays in game.pickups, and the next level's
            # clear_level_objects() calls destroy() on an already-destroyed
            # entity, throws in the middle of switching scenes and dumps you
            # straight back out. That was the "can't reach level 2" bug.
            if self in game.pickups:
                game.pickups.remove(self)
            destroy(self.glow)
            destroy(self.label)
            destroy(self)


class WeaponManager(Entity):
    def __init__(self):
        super().__init__()
        self.guns = []
        self.by_key = {}
        for spec in WEAPONS:
            gun = Weapon(spec)
            self.guns.append(gun)
            self.by_key[spec['key']] = gun
        self.owned = set()
        self.current = None
        self.reset()

    def reset(self):
        self.owned = {s['key'] for s in WEAPONS if s.get('start_with')}
        self.select(next(iter(self.owned)) if self.owned else None)

    def unlock(self, key, announce=False):
        if key in self.owned:
            return
        self.owned.add(key)
        self.select(key)
        if announce:
            spec = self.by_key[key].spec
            flash_title(f'PICKED UP  {spec["name"]}', 1.8)
            beep(pitch=2, length=0.18, wave='sine', volume=0.5)

    def owned_in_order(self):
        return [g for g in self.guns if g.spec['key'] in self.owned]

    def select(self, key):
        for gun in self.guns:
            gun.enabled = False
        self.current = self.by_key.get(key) if key else None
        if self.current and game is not None and game.state in ('doom', 'finale'):
            self.current.enabled = True
            pose_gun_hands(self.current.spec)
        elif gun_hands:
            gun_hands.enabled = False
        refresh_weapon_hud()

    def cycle(self, direction):
        owned = self.owned_in_order()
        if len(owned) < 2:
            return
        i = owned.index(self.current) if self.current in owned else 0
        self.select(owned[(i + direction) % len(owned)].spec['key'])

    def select_slot(self, number):
        if 1 <= number <= len(WEAPONS):
            key = WEAPONS[number - 1]['key']
            if key in self.owned:
                self.select(key)

    def show(self, visible):
        for gun in self.guns:
            gun.enabled = bool(visible and gun is self.current)
        # the arms follow whichever gun is actually out
        pose_gun_hands(self.current.spec if (visible and self.current) else None)
        refresh_weapon_hud()

    def try_fire(self):
        if self.current and self.current.can_fire():
            self.current.fire()


# WeaponManager is created at the end of the HUD section, once the HUD it
# updates actually exists.

# Your old flat viewmodel quad. Kept only as a fallback for when the 3D hand
# model isn't in the project.
viewmodel = Entity(parent=camera.ui, model='quad', origin=(0, -0.5), scale=(0.6, 0.6),
                   position=(0.50, -0.60), rotation_z=-4, z=-1, enabled=False)
TEX_IDLE = safe_texture(HAND_IDLE_FILE)
TEX_GRAB = safe_texture(HAND_GRAB_FILE)
TEX_GUN = safe_texture('ssg2000')

player.holding = 'hand'
player.busy = False
player.creepy = 0
# True when E would do something (answer the phone, open a door). Lean
# checks this so holding E to lean right never swallows an interaction.
player.can_interact = False


def show_viewmodel(state):
    holding_gun = (state == 'gun')
    holding_phone = (state == 'phone')

    if hands_rig:
        hands_rig.enabled = not holding_gun
    if weapons:
        weapons.show(holding_gun)
    if held_phone:
        held_phone.enabled = holding_phone
    if hands_model and not holding_gun:
        # the phone pose brings the arms up and turns them in, so the handset
        # sits against your ear rather than out in front of your chest
        want_pos = HANDS_POS_PHONE if holding_phone else HANDS_POS
        want_rot = HANDS_ROT_PHONE if holding_phone else HANDS_ROT
        hands_model.animate_position(want_pos, duration=0.35, curve=curve.out_quad)
        hands_model.animate_rotation(want_rot, duration=0.35, curve=curve.out_quad)

    if not hands_model:
        # no hand model in the project, fall back to your old flat images
        viewmodel.enabled = not holding_gun
        viewmodel.texture = {'hand': TEX_IDLE, 'grab': TEX_GRAB}.get(state, TEX_IDLE)
        viewmodel.color = color.white if viewmodel.texture else RGB(230, 190, 150)
        return

    viewmodel.enabled = False

    # H still cycles the creepy textures, now tinting the real hands
    if not holding_gun and player.creepy:
        tint = (RGB(150, 190, 150), RGB(200, 130, 130))[player.creepy - 1]
        for part in hands_model.children:
            part.color = tint
    elif hands_model:
        for part in hands_model.children:
            part.color = color.white if part.texture else RGB(214, 178, 156)


show_viewmodel('hand')


def finish_grab():
    player.busy = False
    show_viewmodel(player.holding)


# HOW FAR THE HANDS REACH WHEN YOU PRESS E.
# Halved - it was 0.10 up and 0.22 forward, it is 0.05 and 0.11
# now. I like the movement, just half as much of it, so the
# timing and the curve are untouched: same snap, same settle, shorter reach.
# Raise HAND_PUNCH_REACH.z for more lunge, .y for more of a lift.
HAND_PUNCH_REACH = Vec3(0, 0.05, 0.11)


def hand_punch():
    player.busy = True
    # WHEN the grab started, so do_interact() can tell a real grab apart from a
    # busy flag left stuck up by an invoke() that never came back. See the
    # watchdog in there.
    player.busy_since = time.time()
    if hands_model:
        reach = HANDS_POS_GUN if player.holding == 'gun' else HANDS_POS
        hands_model.animate_position(reach + HAND_PUNCH_REACH,
                                     duration=0.09, curve=curve.out_quad)
        hands_model.animate_position(reach, duration=0.16, delay=0.09)
    else:
        viewmodel.animate_position((0.47, -0.53), duration=0.08, curve=curve.out_quad)
        viewmodel.animate_position((0.50, -0.60), duration=0.14, delay=0.08)
    invoke(finish_grab, delay=0.26)


# ==================================================================
# THE GUN HAND NUDGER
# ==================================================================
# G turns it on. Then the keys listed on WEAPON_GRIP_OFFSET move the hands
# around live, and P prints the numbers to paste back into the file. This
# saved me an enormous amount of restarting.
#
# It edits the OFFSET rather than one weapon, so whatever i settle on applies
# to every gun - which is what i want, because the offset gets added to each
# weapon's own position.
GUN_NUDGE_STEP = 0.012        # metres per key press
GUN_NUDGE_ROT  = 4.0          # degrees per key press
GUN_NUDGE_SCALE = 1.10        # multiplier per key press


class GunHandNudger(Entity):
    def __init__(self):
        super().__init__()
        self.on = False
        self.label = Text('', parent=camera.ui, origin=(0, 0),
                          position=(0, 0.44), scale=0.8,
                          color=RGB(120, 255, 160), enabled=False)
        make_fog_proof(self.label)

    def toggle(self):
        self.on = not self.on
        self.label.enabled = self.on
        self.report(printed=False)
        if self.on:
            print('gun hand nudger ON  -  IJKL move, U/O depth, Y/H size, '
                  'N/M twist, P print, G off')

    def report(self, printed=True):
        o = WEAPON_GRIP_OFFSET
        line = ('WEAPON_GRIP_OFFSET = Vec3(%.3f, %.3f, %.3f)   '
                'GUN_HANDS_SCALE = %.3f   WEAPON_GRIP_ROT = Vec3(%.0f, %.0f, %.0f)'
                % (o.x, o.y, o.z, GUN_HANDS_SCALE, WEAPON_GRIP_ROT.x,
                   WEAPON_GRIP_ROT.y, WEAPON_GRIP_ROT.z))
        self.label.text = 'GUN HANDS  ' + line
        if printed:
            print('\n--- paste these two lines over the ones in the file ---')
            print('WEAPON_GRIP_OFFSET = Vec3(%.3f, %.3f, %.3f)' % (o.x, o.y, o.z))
            print('GUN_HANDS_SCALE = %.3f' % GUN_HANDS_SCALE)
            print('WEAPON_GRIP_ROT = Vec3(%.0f, %.0f, %.0f)\n'
                  % (WEAPON_GRIP_ROT.x, WEAPON_GRIP_ROT.y, WEAPON_GRIP_ROT.z))

    def input(self, key):
        global GUN_HANDS_SCALE
        # DEV ONLY
        # G opens the nudger, and while it is open it grabs I K J L O U Y
        # H N M P - which includes U, your god mode key. With DEV_MODE off
        # it never opens, so none of those are ever intercepted. That is
        # why this guard is on the OPENING key rather than on each nudge.
        if not DEV_MODE:
            return
        if key == 'g':
            self.toggle()
            return
        if not self.on:
            return
        o = WEAPON_GRIP_OFFSET
        s = GUN_NUDGE_STEP
        moved = True
        if key == 'i':
            o.y += s
        elif key == 'k':
            o.y -= s
        elif key == 'j':
            o.x -= s
        elif key == 'l':
            o.x += s
        elif key == 'o':
            o.z += s
        elif key == 'u':
            o.z -= s
        elif key == 'y':
            GUN_HANDS_SCALE *= GUN_NUDGE_SCALE
            if gun_hands:
                gun_hands.scale = GUN_HANDS_SCALE
        elif key == 'h':
            GUN_HANDS_SCALE /= GUN_NUDGE_SCALE
            if gun_hands:
                gun_hands.scale = GUN_HANDS_SCALE
        elif key == 'n':
            WEAPON_GRIP_ROT.x -= GUN_NUDGE_ROT
        elif key == 'm':
            WEAPON_GRIP_ROT.x += GUN_NUDGE_ROT
        elif key == 'p':
            self.report()
            return
        else:
            moved = False
        if moved:
            self.report(printed=False)
            if weapons and weapons.current:
                pose_gun_hands(weapons.current.spec)


gun_nudger = GunHandNudger()


# ==================================================================
# UI - subtitles, prompts, health, fade
# ==================================================================
fade = Entity(parent=camera.ui, model='quad', color=color.black,
              scale=(2, 1.2), z=-2, alpha=0)

sub_bg = Entity(parent=camera.ui, model='quad', color=RGB(0, 0, 0, 170),
                scale=(1.25, 0.16), position=(0, -0.36), z=0.1, enabled=False)
sub_text = Text('', parent=camera.ui, origin=(0, 0), position=(0, -0.36),
                scale=0.95, color=RGB(215, 225, 215), enabled=False)
caller_text = Text('', parent=camera.ui, origin=(0, 0), position=(0, -0.29),
                   scale=0.7, color=RGB(120, 160, 120), enabled=False)

prompt_text = Text('', parent=camera.ui, origin=(0, 0), position=(0, -0.12),
                   scale=1.0, color=RGB(230, 230, 230), enabled=False)

title_text = Text('', parent=camera.ui, origin=(0, 0), position=(0, 0.30),
                  scale=1.6, color=RGB(200, 60, 60), enabled=False)

# health: chunky segments rather than one smooth bar, so you read it at a
# glance and can see exactly how many hits you have left in you
HP_SEGMENTS = 10
hud_root = Entity(parent=camera.ui, enabled=False)

hp_frame = Entity(parent=hud_root, model='quad', color=RGB(10, 8, 10, 210),
                  scale=(0.335, 0.045), position=(-0.60, -0.435))
hp_cells = []
for _i in range(HP_SEGMENTS):
    _w = 0.030
    hp_cells.append(Entity(parent=hud_root, model='quad', color=RGB(200, 40, 40),
                           scale=(_w, 0.026),
                           position=(-0.755 + _i * 0.0325 + _w / 2, -0.435)))
hp_number = Text('100', parent=hud_root, position=(-0.755, -0.395), scale=0.9,
                 color=RGB(210, 90, 90))
hp_label = Text('VITALS', parent=hud_root, position=(-0.505, -0.398), scale=0.55,
                color=RGB(110, 70, 70))

# which gun you're holding, and the slots you've found
weapon_name = Text('', parent=hud_root, origin=(1, 0), position=(0.76, -0.42),
                   scale=1.0, color=RGB(215, 205, 180))
slot_pips = []
for _i in range(len(WEAPONS)):
    slot_pips.append(Entity(parent=hud_root, model='quad', scale=(0.022, 0.022),
                            position=(0.60 + _i * 0.035, -0.465),
                            color=RGB(60, 55, 50)))

# what you're supposed to be doing
objective_text = Text('', parent=hud_root, origin=(0, 0), position=(0, 0.40),
                      scale=0.9, color=RGB(210, 190, 120))

# Top right, comic sans, small, ON SCREEN THE WHOLE GAME - not just in the
# levels, so it is a running total rather than a score. It counts DOOM enemies
LIVER_COUNTER_ON  = True
# measured off your screenshot - 0.92 across, 0.072 down.
# TWICE THE SIZE, AND IT GLOWS
# 1.70 is exactly twice the 0.85 it was. The x moved in from 0.65 to 0.58 to
# pay for it: the text is centred on that point, and at twice the size
# "17 LIVERS" is about 0.27 wide, so at 0.65 the S would have been hanging
# off the right-hand edge of a 16:9 window.
#
# THE GLOW is LiverGlow, further down - it swings the colour between a dull
# blood red and a hot one about three times a second and breathes the size
# with it, which is as annoying as i wanted without being a strobe. Set
# LIVER_GLOW_ON = False and it sits still in LIVER_COUNTER_COLOUR.
LIVER_COUNTER_POS = (0.58, 0.42)      # top right, room for twice the letters
LIVER_COUNTER_SCALE = 1.70            # was 0.85, exactly twice
LIVER_COUNTER_COLOUR = RGB(255, 40, 36)
LIVER_GLOW_ON     = True
LIVER_GLOW_HOT    = RGB(255, 90, 80)    # the bright end of the pulse
LIVER_GLOW_COLD   = RGB(150, 10, 12)    # the dark end
LIVER_GLOW_SPEED  = 10.0                 # pulses a second
LIVER_GLOW_BREATHE = 0.29               # how much the size swings with it
LIVER_LABEL_ONE  = 'LIVER'
LIVER_LABEL_MANY = 'LIVERS'

liver_text = Text('', parent=camera.ui, origin=(0, 0),
                  position=LIVER_COUNTER_POS, scale=LIVER_COUNTER_SCALE,
                  color=LIVER_COUNTER_COLOUR, enabled=LIVER_COUNTER_ON)
make_fog_proof(liver_text)


def refresh_livers():
    if not LIVER_COUNTER_ON or game is None:
        return
    n = game.livers
    global SUB_FONT
    if SUB_FONT is None:
        SUB_FONT = comic_font() or ''
    if SUB_FONT:
        try:
            liver_text.font = SUB_FONT
        except Exception:
            pass
    liver_text.text = '%d %s' % (n, LIVER_LABEL_ONE if n == 1
                                 else LIVER_LABEL_MANY)
    liver_text.enabled = True


class LiverGlow(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)

    def update(self):
        if not (LIVER_GLOW_ON and LIVER_COUNTER_ON) or not liver_text.enabled:
            return
        # 0..1, and squared so it spends longer dark than bright - a throb
        # rather than a sine wave, which reads as something with a pulse
        t = (math.sin(time.time() * math.tau * LIVER_GLOW_SPEED) + 1) * 0.5
        t = t * t
        liver_text.color = mix_color(LIVER_GLOW_COLD, LIVER_GLOW_HOT, t)
        liver_text.scale = LIVER_COUNTER_SCALE * (1 + LIVER_GLOW_BREATHE * t)


liver_glow = LiverGlow()

# compass: a plain strip with a marker that slides as you turn.
compass_line = Entity(parent=hud_root, model='quad', scale=(COMPASS_WIDTH, 0.0025),
                      position=(0, COMPASS_Y), color=RGB(220, 220, 220, 70))
for _t in (-1, -0.5, 0, 0.5, 1):
    Entity(parent=compass_line, model='quad', scale=(0.006 / COMPASS_WIDTH, 2.6),
           position=(_t * 0.5, 0), color=RGB(220, 220, 220, 55))
compass_marker = Entity(parent=hud_root, model='quad', scale=0.014, rotation_z=45,
                        position=(0, COMPASS_Y + 0.013), color=RGB(255, 210, 90))
compass_distance = Text('', parent=hud_root, origin=(0, 0),
                        position=(0, COMPASS_Y - 0.028), scale=0.55,
                        color=RGB(190, 175, 130))

# damage: the vignette from the Sandbox assets, punched red when you're hit
damage_flash = Entity(parent=camera.ui, model='quad',
                      texture=safe_texture('vignette'),
                      color=RGB(255, 30, 30), scale=(2, 1.2), z=-1.5, alpha=0)
if damage_flash.texture is None:
    damage_flash.color = RGB(255, 0, 0, 90)


def set_hud(on):
    hud_root.enabled = on


def refresh_health():
    ratio = max(0.0, player.health / PLAYER_MAX_HP)
    lit = ratio * HP_SEGMENTS
    for i, cell in enumerate(hp_cells):
        if i + 1 <= lit:
            full = True
        elif i < lit:
            full = None            # the part-filled one
        else:
            full = False
        if full is False:
            cell.color = RGB(45, 18, 18)
        else:
            hot = RGB(220, 60, 50) if ratio > 0.35 else RGB(255, 150, 40)
            cell.color = hot if full else RGB(120, 35, 30)
    hp_number.text = str(int(max(0, player.health)))
    hp_number.color = RGB(215, 90, 90) if ratio > 0.35 else RGB(255, 160, 60)


def refresh_weapon_hud():
    if weapons is None:
        return
    weapon_name.text = weapons.current.spec['name'] if weapons.current else ''
    for i, spec in enumerate(WEAPONS):
        owned = spec['key'] in weapons.owned
        held = weapons.current is not None and weapons.current.spec['key'] == spec['key']
        if held:
            slot_pips[i].color = RGB(255, 215, 120)
        elif owned:
            slot_pips[i].color = RGB(130, 120, 95)
        else:
            slot_pips[i].color = RGB(48, 45, 42)


# CROSSHAIR: four small ticks and a dot, much tighter than Ursina's default
# pink diamond, which gets replaced here. FirstPersonController owns this and
# switches it back on by itself, so it gets emptied out as well as disabled -
# that is the dot that kept coming back no matter what i did.
player.cursor.enabled = False
player.cursor.color = color.clear
player.cursor.scale = 0
# No centre dot at all - four hairline ticks around an empty middle, so
# nothing sits on top of what you're aiming at.
crosshair = Entity(parent=camera.ui, enabled=False)
for _dx, _dy, _sx, _sy in ((0.0075, 0, 0.005, 0.0011), (-0.0075, 0, 0.005, 0.0011),
                           (0, 0.0075, 0.0011, 0.005), (0, -0.0075, 0.0011, 0.005)):
    Entity(parent=crosshair, model='quad', position=(_dx, _dy),
           scale=(_sx, _sy), color=RGB(235, 240, 245, 150))


# ==================================================================
# THE HITMARKER
# ==================================================================
# ----------------------------------------------------------------------
# Four ticks at 45 degrees around the crosshair, which appear the instant a
# shot lands on something alive and fade out on their own. The whole point is
# that it is INSTANT and it is at the centre of the screen, where you are
# already looking - you should never have to check whether a shot connected.
#
# It is one node with four children, built once and reused, never created per
# hit: at a minigun's fourteen rounds a second, building and destroying
# entities would cost more than the shooting does.
#
# A KILL IS DIFFERENT: bigger, red, up for twice as long, and a lower note. So
# "I am hurting it" and "it is down" are two different signals and you do not
# have to look away from where you are aiming to tell them apart.
class HitMarker(Entity):
    def __init__(self):
        super().__init__()
        self.root = Entity(parent=camera.ui, enabled=False)
        self.ticks = []
        for dx, dy, rot in ((-1, 1, -45), (1, 1, 45), (-1, -1, 45), (1, -1, -45)):
            t = Entity(parent=self.root, model='quad', rotation_z=rot,
                       position=(dx * HITMARKER_GAP, dy * HITMARKER_GAP),
                       scale=(HITMARKER_SIZE, HITMARKER_SIZE * 0.26),
                       color=HITMARKER_COLOUR, unlit=True)
            self.ticks.append(t)
        make_fog_proof(self.root)
        # over the world and the hands, under the text box and the adverts
        ad_layer(self.root, 260)
        # NOT self.left / self.life. `left` is already an Entity property - it
        # is the direction vector out of your left shoulder - and assigning to
        # it raises "can't set attribute" with no hint as to which attribute.
        # It is the same trap PlayerSettler's docstring warns about further
        # down, and I walked straight into it. Any short spatial word on an
        # Entity is taken: left, right, up, down, forward, back, world_*.
        self.marker_left = 0.0
        self.marker_life = HITMARKER_TIME

    def hit(self, kill=False):
        if not HITMARKER_ON:
            return
        k = HITMARKER_KILL_SCALE if kill else 1.0
        for t, (dx, dy) in zip(self.ticks, ((-1, 1), (1, 1), (-1, -1), (1, -1))):
            t.color = HITMARKER_KILL if kill else HITMARKER_COLOUR
            t.scale = (HITMARKER_SIZE * k, HITMARKER_SIZE * 0.26 * k)
            t.position = (dx * HITMARKER_GAP * k, dy * HITMARKER_GAP * k)
        self.marker_life = HITMARKER_KILL_TIME if kill else HITMARKER_TIME
        self.marker_left = self.marker_life
        self.root.enabled = True
        if HITMARKER_SOUND:
            if kill:
                beep(pitch=-6, length=0.09, wave='square', volume=0.30)
            else:
                beep(pitch=10, length=0.045, wave='square', volume=0.18)

    def update(self):
        if self.marker_left <= 0:
            return
        self.marker_left -= time.dt
        if self.marker_left <= 0:
            self.root.enabled = False
            return
        # they fade AND drift outward, which reads as an impact rather than a
        # light switching off
        k = self.marker_left / max(0.0001, self.marker_life)
        spread = 1.0 + (1.0 - k) * 0.5
        for t, (dx, dy) in zip(self.ticks, ((-1, 1), (1, 1), (-1, -1), (1, -1))):
            base = HITMARKER_GAP * (HITMARKER_KILL_SCALE
                                    if t.color == HITMARKER_KILL else 1.0)
            t.position = (dx * base * spread, dy * base * spread)
            t.alpha = k


hitmarker = HitMarker()


# Everything the weapons need now exists, so they can be built.
weapons = WeaponManager()
refresh_weapon_hud()

# THE GUNS AND THE UI ARE FOG-PROOFED TOO. This is the other half of the fix
# started up in SECTION 7 - the weapons are viewmodel objects exactly like
# the hands, and the DOOM fog was getting onto the gun textures. Every gun
# model, the spinning minigun barrel, the flat fallback hand sprite and every
# 2D overlay opts out of fog here, once and for all.
make_fog_proof(viewmodel, crosshair, hud_root, fade, damage_flash,
               sub_bg, sub_text, caller_text, prompt_text, title_text)
for _g in weapons.guns:
    make_fog_proof(_g, getattr(_g, 'barrel', None))
print('weapons + UI: exempted from fog')


# The three widgets get built much further down, near the bench guys. I name
# them here so show_prompt() - which gets called from all over this file, and
# from the very first frame - can talk to them before they exist without
# needing a special case anywhere.
talk_box = None
prompt_box = None
handler_head = None


def show_prompt(msg):
    if PROMPTS_IN_BOX and prompt_box is not None:
        prompt_text.enabled = False
        prompt_box.show(msg)
        return
    prompt_text.text = msg
    prompt_text.enabled = bool(msg)


def flash_notice(msg, seconds=None, quiet=False):
    if prompt_box is not None:
        prompt_box.notice(msg, seconds, quiet=quiet)
    else:
        print('[notice]', msg)


def flash_title(msg, seconds=2.5):
    title_text.text = msg
    title_text.enabled = True
    title_text.alpha = 1
    title_text.animate('alpha', 0, duration=seconds, delay=0.6)
    invoke(setattr, title_text, 'enabled', False, delay=seconds + 0.8)


def fade_to_black(duration=0.7, then=None):
    fade.animate('alpha', 1, duration=duration)
    if then:
        invoke(then, delay=duration + 0.05)


def fade_from_black(duration=0.9):
    fade.alpha = 1
    fade.animate('alpha', 0, duration=duration)


# ==================================================================
# VOICE - the spoken lines
# ==================================================================
SUB_WORDS_PER_BURST = (3, 4)
def rainbow_colour(seed=None):
    if seed is None:
        return random.choice(SUB_COLOURS)
    return SUB_COLOURS[abs(hash(seed)) % len(SUB_COLOURS)]


SUB_COLOURS = [
    RGB(255, 60, 190), RGB(90, 255, 90),  RGB(255, 230, 40),
    RGB(60, 200, 255), RGB(255, 120, 20), RGB(190, 90, 255),
    RGB(255, 255, 255), RGB(255, 40, 40), RGB(40, 255, 210),
]
# Ursina's text scale 1.0 is roughly a 16pt glyph, so this tops out just under
# 15pt and still varies enough to read as chaotic. Nothing is ever rotated.
SUB_SCALE_RANGE = (0.55, 0.92)
# Kept off the very edges, and out of the middle band where you're aiming.
SUB_X_RANGE = (-0.62, 0.52)
SUB_Y_RANGE = (-0.40, 0.42)
SUB_FONTS = ['comic.ttf', 'ComicSansMS.ttf', 'comici.ttf']


def comic_font():
    for name in SUB_FONTS:
        if find_asset(name):
            return name
    return None


SUB_FONT = None          # resolved on first use, once ASSETS is walkable


class VoicePlayer(Entity):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.index = -1
        self.timer = 0
        self.playing = False
        self.on_finish = None
        self.clip = None
        self.bursts = []         # the 3-4 word chunks of the current line
        self.burst_i = 0
        self.shown = []          # Text entities currently on screen

    def clear_bursts(self):
        for t in self.shown:
            try:
                destroy(t)
            except Exception:
                pass
        self.shown = []

    def show_burst(self, words):
        global SUB_FONT
        if SUB_FONT is None:
            SUB_FONT = comic_font() or ''
        t = Text(' '.join(words), parent=camera.ui, origin=(0, 0),
                 position=(random.uniform(*SUB_X_RANGE),
                           random.uniform(*SUB_Y_RANGE)),
                 scale=random.uniform(*SUB_SCALE_RANGE),
                 color=random.choice(SUB_COLOURS))
        if SUB_FONT:
            try:
                t.font = SUB_FONT
            except Exception:
                pass
        t.rotation_z = 0          # dead level - no tilt, no twitch
        t.animate('alpha', 0, duration=2.6, delay=1.1)
        self.shown.append(t)
        # never let more than a handful pile up
        while len(self.shown) > 7:
            old = self.shown.pop(0)
            try:
                destroy(old)
            except Exception:
                pass

    def split_line(self, line):
        words = line.split()
        out, i = [], 0
        while i < len(words):
            n = random.randint(*SUB_WORDS_PER_BURST)
            out.append(words[i:i + n])
            i += n
        return out

    def play(self, lines, on_finish=None, audio_name=None, caller='HIM',
             handler=False, chapter=None, finale=None):
        self.lines = list(lines)
        self.index = -1
        self.playing = True
        self.on_finish = on_finish
        self.burst_gap = 0.5
        self.burst_timer = 0.0
        self.handler = handler
        self.clear_bursts()
        # HIS VOICE
        # EVERY line that comes through VoicePlayer is him: the phone calls,
        # the DOOM level, the last confrontation and the endings that follow
        # it. So the box always speaks in the handler's voice here, and 'him'
        # gets passed rather than left to the default, so that reading this
        # one line tells you whose voice you are about to hear.
        #
        # The pitch ladder only steps on a CALL - handler=True - because that
        # is the thing that happens over and over. The finale and the endings
        # are once each and would only jump him two rungs at the end for no
        # reason.
        if handler:
            handler_voice_step_up()
        if VOICE_IN_TALK_BOX and talk_box is not None:
            talk_box.open_for_voice(HANDLER_NAME if handler else caller,
                                    voice_clip='him',
                                    chapter=chapter, finale=finale)
            if handler and handler_head is not None:
                handler_head.show()
        # the tidy black caption bar is gone - the scattered bursts ARE the
        # subtitles now. Flip these back to True to get the old bar back.
        sub_bg.enabled = False
        sub_text.enabled = False
        caller_text.enabled = not VOICE_IN_TALK_BOX
        caller_text.text = caller
        # PER-CHAPTER VOICE FILES. voice_0.wav, voice_1.wav and so on were
        # never in the project - I checked every audio file in the tree - so
        # this only ever printed "no audio found with name: voice_3" twice
        # per phone call. His voice comes from the talk box now
        # (HANDLER_VOICE_STAGES), which is a real file that really plays.
        #
        # The hook is kept because per-chapter recordings are a good idea and
        # you may well want them. Drop voice_0.wav .. voice_5.wav in the
        # project, set CHAPTER_VOICE_FILES = True, and they play over the
        # top of the box exactly as intended.
        if audio_name and CHAPTER_VOICE_FILES:
            self.clip = safe_audio(audio_name, autoplay=True, volume=0.9)
        self._advance()

    def _advance(self):
        self.index += 1
        if self.index >= len(self.lines):
            self.stop()
            return
        line = self.lines[self.index]
        sub_text.text = ''              # the tidy caption bar stays empty now
        self.bursts = [] if VOICE_IN_TALK_BOX else self.split_line(line)
        self.burst_i = 0
        if VOICE_IN_TALK_BOX and talk_box is not None:
            talk_box.set_line(line, '[E]  skip')
        # roughly reading speed, with a floor so short lines still land
        self.timer = max(1.9, len(line) * 0.055)
        self.burst_gap = self.timer / max(1, len(self.bursts))
        self.burst_timer = 0.0

    def skip(self):
        if self.playing:
            self._advance()

    def stop(self):
        self.playing = False
        self.clear_bursts()
        sub_bg.enabled = False
        sub_text.enabled = False
        caller_text.enabled = False
        # the call is over, so the box closes and the head stops
        if talk_box is not None and talk_box.driven_by_voice:
            talk_box.close()
        if handler_head is not None:
            handler_head.hide()
        if self.clip:
            try:
                self.clip.stop()
            except Exception:
                pass
            self.clip = None
        callback, self.on_finish = self.on_finish, None
        if callback:
            callback()

    def update(self):
        if not self.playing:
            return
        # spill the next 3-4 words onto the screen
        if self.burst_i < len(self.bursts):
            self.burst_timer -= time.dt
            if self.burst_timer <= 0:
                self.show_burst(self.bursts[self.burst_i])
                self.burst_i += 1
                self.burst_timer = self.burst_gap
        self.timer -= time.dt
        if self.timer <= 0:
            self._advance()


voice = VoicePlayer()


# ==================================================================
# THE OFFICE - the first room
# ==================================================================
office_root = Entity(enabled=False)

# THE APARTMENT'S ROOT, CREATED HERE AND FILLED IN LATER.
# It is empty until build_apartment() runs near the end of the file, but it
# has to EXIST from here on, because the finale's walk-out door gets parented
# to it a few hundred lines below and Python resolves that at import time. If
# i define it down with the rest of the apartment the game will not start.
apartment_root = Entity(enabled=False, position=APARTMENT_AT)

# THE WORLD OUTSIDE. Created here at the top rather than down in SECTION 12b
# where it used to be, because the red door into DOOM is now parented to it
# (see the note on DOOM_DOOR_POS) and Python has to have made it before
# anything can reference it. Everything that used to hang off it still does -
# only the one line moved.
city_root = Entity(enabled=False)

# NO OFFICE FLOOR ANY MORE.
# There used to be a 30x30m dark slab here. Standing in the middle of the
# cemetery it was a 900 square metre lid over the graves, which is a large
# part of why the grass looked buried - anything within 15m of the desk was
# under it. The cemetery terrain is the ground for this scene now: one
# surface, checked first, for everything.
#
# All that is left is a small pad directly under the desk, so the chair and
# the table legs have something dead flat to stand on rather than following
# every bump in a photogrammetry scan. It is 4m across and sits a centimetre
# down, so it reads as the ground rather than as a platform.
#
# ---- IT SAYS "MONTHLY SUBSCRIPTION" NOW ----
# Doubled, 4m to 8m across, so the lettering is big enough to actually read
# while you are standing at the desk looking down at it.
#
# It is a cube plus a separate quad lying on top, and the quad is the whole
# reason this works: Ursina's cube maps the same image onto all six faces, so
# the top face showed the picture sideways or cropped depending on the model's
# UVs. A quad laid flat, rotated 90 on X and given the texture straight,
# cannot be anything but the full image the right way up. It floats 6mm above
# the cube's top face so the two never z-fight.
OFFICE_PAD_SIZE    = 8.0                    # was 4.0
OFFICE_PAD_TEXTURE = 'monthlysubscription'  # the ironic bit

office_pad = Entity(parent=office_root, model='cube',
                    scale=(OFFICE_PAD_SIZE, 0.10, OFFICE_PAD_SIZE),
                    position=(0, -0.05, 0.8), color=RGB(22, 21, 24),
                    collider='box', unlit=True)

_pad_tex = crunchy_texture(None, OFFICE_PAD_TEXTURE)
if _pad_tex is None:
    print('!! %s.png not found - the pad under the office stays plain black. '
          'Put it anywhere in the project.' % OFFICE_PAD_TEXTURE)
office_pad_face = Entity(parent=office_root, model='quad', rotation_x=90,
                         position=(0, 0.006, 0.8),
                         scale=(OFFICE_PAD_SIZE, OFFICE_PAD_SIZE),
                         texture=_pad_tex,
                         color=color.white if _pad_tex else RGB(22, 21, 24),
                         unlit=True, double_sided=True)

# The old "Office Desk.obj" is gone - the cubicle .glb below replaces it
# entirely, and it comes with its own desk, chair, monitor and partitions.

# The invisible walls that used to box you in are gone on purpose - you can
# now walk straight out of the office and into the city.

# A real cubicle: partitions, desk, chair, monitor. It sits where the old
# desk did, turned so you're looking straight at the desk when the game opens.
office_room = None
office_desk_top = None      # filled in once we can raycast, see find_desk_top()

def build_desk_set():
    obj = find_asset(OFFICE_DESK_OBJ)
    if obj is None:
        print(f'!! {OFFICE_DESK_OBJ} not found - falling back to the cubicle')
        return None
    holder = Entity(parent=office_root, position=OFFICE_DESK_POS,
                    rotation=OFFICE_DESK_ROT, scale=OFFICE_DESK_SCALE)
    groups = load_obj_by_material(obj, flip_x=False, shade=True)
    tris = 0
    unmapped, notex = [], []
    for name, (vlist, ulist, clist) in groups.items():
        if not vlist:
            continue
        tris += len(vlist) // 3
        # case-insensitive, so 'Monitor' in the file finds 'monitor' in
        # the table and vice versa. That single capital letter is what left the
        # monitor flat grey.
        tex_name = OFFICE_DESK_TEXTURES_CI.get(name.lower())
        if tex_name is None:
            unmapped.append(name)
        tex = crunchy_texture(obj.parent, tex_name) if tex_name else None
        if tex_name and tex is None:
            notex.append('%s->%s' % (name, tex_name))
        piece = Entity(parent=holder,
                       model=Mesh(vertices=vlist, uvs=ulist, colors=clist,
                                  mode='triangle', static=True),
                       texture=tex,
                       color=color.white if tex else RGB(170, 165, 155),
                       double_sided=True, unlit=True)
        piece.group_name = name
    print('desk set: %d triangles across %d objects, %d textured'
          % (tris, len(groups), len(groups) - len(unmapped) - len(notex)))
    # SAID OUT LOUD, not painted grey in silence. Every "why is that thing not
    # textured" bug in this project has been one of these two lines.
    if unmapped:
        print('   !! desk groups with NO entry in OFFICE_DESK_TEXTURES (they '
              'render flat grey): %s' % ', '.join(unmapped))
    if notex:
        print('   !! desk textures named but the FILE is missing: %s'
              % ', '.join(notex))

    # A couple of boxes so you can't walk through the desk or the chair. Much
    # cheaper than a mesh collider on 20k triangles, and it feels identical.
    Entity(parent=holder, model='cube', collider='box', visible=False,
           position=(0.21, OFFICE_DESK_TOP / 2, 1.17),
           scale=(0.90, OFFICE_DESK_TOP, 2.05))            # the table
    Entity(parent=holder, model='cube', collider='box', visible=False,
           position=(0.95, 0.45, 0.77), scale=(0.95, 0.90, 0.90))   # the chair

    # YOU CANNOT CLIMB ONTO THE DESK OR THE CHAIR
    # The trick is that the collider carries on straight up into the sky, so
    # there is no top surface to land on. You still jump normally everywhere
    # else - this is not a global "no jumping" switch, it is two invisible
    # pillars standing on these two bits of furniture.
    #
    # They start just above the desktop, so you can still walk right up to the
    # desk and the phone is still reachable, and run up to NO_CLIMB_TOP. Jump
    # at the desk now and you bump your head instead of ending up standing on
    # your own paperwork.
    for px, py, pz, sx, sz, label in (
            (0.21, OFFICE_DESK_TOP, 1.17, 0.90, 2.05, 'table'),
            (0.95, 0.90, 0.77, 0.95, 0.90, 'chair')):
        pillar = Entity(parent=holder, model='cube', collider='box',
                        visible=False,
                        position=(px, py + NO_CLIMB_TOP / 2, pz),
                        scale=(sx, NO_CLIMB_TOP, sz))
        # BUT YOU CAN STILL REACH THE PHONE THROUGH IT
        # These pillars stand in the air right where you look to press E on
        # the phone, so the interact ray was hitting an invisible box and
        # stopping there. Tagging them means do_interact() looks straight
        # through them - they block your BODY, not your eyes.
        pillar.no_climb = True
        no_climb_boxes.append(pillar)

    # THE COMPUTER IS SHOWING THE SPREADSHEET
    # OFFICE_SCREEN_TEXTURE is None now, so the quad does not get built at
    # all - which is what getting rid of it completely should mean. It is not
    # built and hidden, and it does not print a missing-file warning either.
    if OFFICE_SCREEN_ON and OFFICE_SCREEN_TEXTURE:
        stex = crunchy_texture(None, OFFICE_SCREEN_TEXTURE)
        if stex is None:
            print('!! %s.png is not in the project, so the monitor '
                  'stays blank. Drop the file anywhere under the project '
                  'folder and it appears - nothing else needs changing.'
                  % OFFICE_SCREEN_TEXTURE)
        else:
            Entity(parent=holder, model='quad',
                   position=OFFICE_SCREEN_POS,
                   rotation=(0, OFFICE_SCREEN_YAW, 0),
                   scale=OFFICE_SCREEN_SIZE,
                   texture=stex, color=color.white,
                   unlit=OFFICE_SCREEN_UNLIT, double_sided=True)
            print('   monitor: showing %s' % OFFICE_SCREEN_TEXTURE)
    return holder


office_desk_set = build_desk_set() if OFFICE_USE_DESK_SET else None

_room_file = None if office_desk_set else find_asset(f'{OFFICE_GLB}.glb')
if _room_file:
    office_room = Entity(parent=office_root, model=OFFICE_GLB,
                         scale=OFFICE_GLB_SCALE, position=OFFICE_GLB_POS,
                         rotation=OFFICE_GLB_ROT)
    _b = office_room.model.getTightBounds()
    if _b:
        _oh = (_b[1][1] - _b[0][1]) * OFFICE_GLB_SCALE
        print('office: %.1f x %.1f x %.1fm  (player eye is %.2fm)'
              % ((_b[1][0] - _b[0][0]) * OFFICE_GLB_SCALE, _oh,
                 (_b[1][2] - _b[0][2]) * OFFICE_GLB_SCALE, PLAYER_HEIGHT))
        _eye = EYE_HEIGHT.get('office', PLAYER_HEIGHT)
        if _oh < _eye + 0.15:
            print(f'   !! the office is {_oh:.1f}m tall and your eyes are at '
                  f'{_eye:.1f}m in this scene - your head is near the ceiling.')
            print(f'   !! raise OFFICE_GLB_SCALE to about '
                  f'{(_eye + 0.5) / (_b[1][1] - _b[0][1]):.2f}, or lower '
                  f"EYE_HEIGHT['office'].")

    # Solid, so you can't walk through the partitions or the desk. A mesh
    # collider is fine here now the model is 27k triangles rather than 329k
    # and it means the phone can be placed by raycasting onto the real desk
    # instead of me guessing coordinates.
    office_room.collider = 'mesh'


def find_desk_top():
    global office_desk_top
    if office_desk_top is not None or not office_room:
        return office_desk_top
    best = None
    x = -1.4
    while x <= 1.4:
        z = -0.2
        while z <= 2.2:
            hit = raycast(Vec3(x, 2.4, z), Vec3(0, -1, 0), distance=2.6,
                          ignore=(player,), traverse_target=office_room)
            if hit.hit and 0.45 < hit.world_point.y < 1.3:
                if best is None or hit.world_point.y > best.y:
                    best = hit.world_point
            z += 0.25
        x += 0.25
    office_desk_top = best
    if best:
        print('desk surface found at %.2f, %.2f, %.2f' % (best.x, best.y, best.z))
    return best

# the phone. small, warm, and it glows when it wants you.
# A proper handset shape rather than a black slab, and no glow on it - the
# lamp above the desk is what draws your eye now.
phone = Entity(parent=office_root, model='cube', position=PHONE_POS,
               scale=(0.17, 0.05, 0.10),
               texture=crunchy_texture(None, PHONE_TEXTURE),
               color=color.white, collider='box', unlit=True)
# The handset and cord used to be two extra plain dark cubes stacked on the
# textured base - that is the "two phones" that were on the desk. They are
# gone. What is left is the one textured object, and the ringing shows by
# brightening that instead of by lighting up a second block.
#
# Both names survive because the ringing and the endings talk to them; they
# just do not draw anything now.
phone_handset = Entity(parent=phone, visible=False, scale=0.001)
phone_cord = Entity(parent=phone, visible=False, scale=0.001)
PHONE_DIM = RGB(140, 138, 142)      # resting tint on the textured phone
phone.color = PHONE_DIM


def seat_office_on_ground():
    if OFFICE_IN_APARTMENT:
        return                      # the desk is indoors
    if terrain_height is None:
        return
    was = city_root.enabled
    city_root.enabled = True            # the ray needs the terrain switched on
    try:
        y = ground_under(OFFICE_ORIGIN_XZ.x, OFFICE_ORIGIN_XZ.y)
    finally:
        city_root.enabled = was
    # a few centimetres of clearance, so the desk and chair are unambiguously
    # standing ON the grass rather than level with it
    office_root.position = Vec3(OFFICE_ORIGIN_XZ.x, y + OFFICE_GROUND_LIFT,
                                OFFICE_ORIGIN_XZ.y)
    # turned so the chair is the nearest thing to you when you arrive
    office_root.rotation_y = OFFICE_FACING


def seat_phone_on_desk():
    if office_desk_set is not None:
        spot = Vec3(PHONE_POS.x, PHONE_POS.y, PHONE_POS.z)
        for part in lamp_parts:
            part.x = spot.x
            part.z = spot.z
            if part.model_name_hint == 'pool':
                part.y = spot.y + 0.004
        lamp_light.position = (spot.x, spot.y + 1.35, spot.z)
        return
    top = find_desk_top()
    if not top:
        return
    spot = Vec3(top.x, top.y + 0.024, top.z)
    phone.position = spot
    for part in lamp_parts:
        part.x = spot.x
        part.z = spot.z
        if part.model_name_hint == 'pool':
            part.y = spot.y + 0.004
    lamp_light.position = (spot.x, spot.y + 1.35, spot.z)
phone.is_phone = True
# the glow pool is gone. this entity stays so the ringing code has something to talk to, but it never draws
phone_glow = Entity(parent=office_root, model='quad', position=PHONE_POS + Vec3(0, 0.02, 0),
                    rotation_x=90, scale=0.9, color=RGB(255, 190, 90, 0),
                    unlit=True, double_sided=True, enabled=False)

# Built in layers rather than as one flat quad: a bright core on the desk, two
# wider falloff pools, a cone of haze hanging in the air, and the bulb itself.
lamp_parts = []


def _lamp(model, pos, scale, col, rot=(0, 0, 0), weight=1.0, dbl=True, hint='pool'):
    # ONE LAYER OF THE DESK LAMP. The lamp is built out of several of these
    # stacked up - a bright pool on the desk, wider softer pools around it, a
    # cone of haze in the air and the bulb - because there are no real lights
    # in this game, so a glow has to be faked out of flat shapes.
    e = Entity(parent=office_root, model=model, position=pos, scale=scale,
               rotation=rot, color=col, unlit=True, double_sided=dbl,
               enabled=OFFICE_LAMP)
    e.base_color = col
    e.weight = weight            # how much of the flicker this layer takes
    e.model_name_hint = hint     # 'pool' sits on the desk, others float above
    lamp_parts.append(e)
    return e


# THE POOLS ARE ON THE FLOOR NOW, not on the desktop.
# They used to sit at y=0.80 - desk height - and that is the hard edge i could
# see: the quad ended exactly where the desk did, because it WAS at the desk's
# height and the desk's geometry cut across it. Dropping them to y=0.01 puts
# them below your feet, where you cannot see where they stop.
#
# They are also much fainter and much wider now, so it reads as a room that
# happens to be lit rather than a spotlight with a rim round it.
_lamp('quad', (0, 0.012, 0.73), (4.5, 3.2), RGB(255, 236, 200, 26), (90, 0, 0), 1.0)
_lamp('quad', (0, 0.010, 0.73), (7.5, 5.5), RGB(255, 214, 150, 15), (90, 0, 0), 0.9)
_lamp('quad', (0, 0.008, 0.73), (11.0, 8.0), RGB(255, 190, 120, 8), (90, 0, 0), 0.7)
# the cone of dusty air under the shade
def light_cone(segments=20, top_radius=0.10):
    verts = []
    for i in range(segments):
        a1 = i / segments * math.tau
        a2 = (i + 1) / segments * math.tau
        low1 = (math.cos(a1), 0, math.sin(a1))
        low2 = (math.cos(a2), 0, math.sin(a2))
        top1 = (math.cos(a1) * top_radius, 1, math.sin(a1) * top_radius)
        top2 = (math.cos(a2) * top_radius, 1, math.sin(a2) * top_radius)
        verts += [low1, low2, top2, low1, top2, top1]
    return Mesh(vertices=verts, mode='triangle', static=True)


# the shaft of light hanging under the shade, in two layers
# The haze cone now starts at the FLOOR and runs to the bulb, so it has no
# visible bottom edge either. Much fainter - it should suggest dust, not fog.
_lamp(light_cone(), (0, 0.01, 0.73), (1.9, 2.15, 1.9), RGB(255, 210, 150, 6), (0, 0, 0), 0.8)
_lamp(light_cone(top_radius=0.06), (0, 0.01, 0.73), (1.0, 2.13, 1.0),
      RGB(255, 230, 185, 8), (0, 0, 0), 0.9)
# the bulb
lamp_bulb = _lamp('sphere', (0, 2.16, 0.73), 0.13, RGB(255, 245, 215, 255), weight=1.0)
_lamp('sphere', (0, 2.16, 0.73), 0.30, RGB(255, 226, 170, 60), weight=1.0)

# A REAL LIGHT, SO THE DESK AND YOUR HANDS ACTUALLY CATCH IT - except it is
# OFF BY DEFAULT, and it is what was blowing out the hands. A Panda3D
# PointLight lights every lit object in the scene, and while the hands are
# drawn on their own display region they are still ordinary nodes under the
# same render state - so the lamp reached them and washed them to white from
# about a metre away.
#
# Everything in the office is unlit=True and gets its look from the fog and
# the vertex shading instead, so nothing actually needed a real light. Set
# OFFICE_REAL_LIGHT = True if i ever want it back.
OFFICE_REAL_LIGHT = False
lamp_light = PointLight(parent=office_root, position=(0, 2.1, 0.73),
                        color=RGB(255, 224, 178), shadows=False)
lamp_light.enabled = OFFICE_REAL_LIGHT


class LampFlicker(Entity):
    def __init__(self):
        super().__init__()
        self.level = 1.0            # current brightness, 0..1
        self.next_event = 2.0       # seconds until the next disturbance
        self.burst = 0              # stutters left in this burst
        self.burst_gap = 0.0
        self.distance_fade = 1.0

    def schedule(self):
        # long calm stretches, occasionally a very short one - so you can never
        # quite predict it
        self.next_event = random.choice([
            random.uniform(3.0, 9.0),
            random.uniform(0.4, 1.6),
        ])
        self.burst = random.randint(1, 5)

    def update(self):
        if not OFFICE_LAMP:          # set that to False and the lamp is gone
            return
        if game is None or not office_root.enabled:
            return

        # The lamp is simply ON while you are in the room and OFF once you are
        # out of it - no gradient. game.office_pull is already that test, so
        # the lamp and the fog can never disagree about where the room ends.
        target = game.office_pull if game.state == 'office' else 0.0
        self.distance_fade = lerp(self.distance_fade, target,
                                  min(1, time.dt * OFFICE_FADE_SPEED))

        # the flicker
        if self.burst > 0:
            self.burst_gap -= time.dt
            if self.burst_gap <= 0:
                self.burst -= 1
                self.burst_gap = random.uniform(0.03, 0.13)
                self.level = random.uniform(0.05, 0.45) if self.level > 0.6 else 1.0
                if self.burst <= 0:
                    self.level = 1.0
                    self.schedule()
        else:
            self.next_event -= time.dt
            self.level = lerp(self.level, 1.0, min(1, time.dt * 10))
            if self.next_event <= 0:
                self.burst_gap = 0
                self.schedule()
                self.burst = random.randint(2, 6)

        brightness = self.level * self.distance_fade
        for part in lamp_parts:
            base = part.base_color
            k = 1 - part.weight + part.weight * brightness
            part.color = color.rgba(base[0], base[1], base[2], base[3] * k)
        if OFFICE_REAL_LIGHT:
            lamp_light.color = color.rgba(1.0, 0.88, 0.70, 1.0) * max(0.02, brightness)
            lamp_light.enabled = brightness > 0.02


lamp_flicker = LampFlicker()

# The way into the level. Hidden until he's finished talking. Off to the right
# so you don't have to squeeze past the desk in the dark to reach it.
# Off to the LEFT, clear of the cubicle partitions, wearing one of DOOM's own
# door textures so it reads as a way out rather than a red slab. No floating
# label over it - if you've just been told to go through a door, you'll find it.
# On the RIGHT, tucked against the office rather than out in a corridor, and
# sized to stand properly on the ground rather than floating.
# YOUR COORDINATES, USED AS WORLD COORDINATES.
#
# The door is parented to city_root rather than office_root now, and that is
# the important bit: office_root is moved to sit on the grass AND turned by
# OFFICE_FACING (90 degrees), so anything parented to it has its coordinates
# rotated and shifted before they reach the world. The numbers i read off
# with T are world numbers, so putting them into a child of office_root would
# have landed the door about 22 metres from where i wanted it, turned
# sideways. city_root sits at the origin unrotated, so what i typed is
# where it goes.
#
# city_root is also enabled in exactly the scenes the door should exist in -
# the office and the village - and off everywhere else, so it can never turn
# up in the middle of the finale.
#
# ---------- MOVED IN, AND THREE TIMES THE SIZE ----------
# Your new coordinate. It was at x 22.25, which you found too far out; this is
# 12.85, about nine metres closer to the desk.
#
# THREE TIMES BIGGER, on every axis: 0.20 x 2.1 x 1.5 becomes 0.60 x 6.3 x 4.5.
# So it is a 4.5m wide, 6.3m tall slab - it does not read as a door you walk
# through any more, it reads as something that has opened in the world, which
# is the right instinct for where it goes.
#
# AND IT CANNOT SPAWN UNDERGROUND. tripling a door positioned by its CENTRE would sink it two metres into the
# a door that is positioned by its CENTRE would sink it two metres into the
# ground. It is placed by its FLOOR instead - centre = your y + half the
# height - so the bottom edge sits exactly on the 0.04 you read off with T no
# matter what size you make it. Change DOOM_DOOR_SIZE to anything you like and
# that stays true.
#
# WHICH WAY IT LOOKS: at the office. You come at it from the desk side, so its
# face has to point back that way - the target below is the office origin, not
# a fixed coordinate, so if you ever move the office the door turns to follow.
DOOM_DOOR_POS   = Vec3(12.85, 0.04, -0.37)     # yours
DOOM_DOOR_FACES = Vec3(0.0, 0.04, -0.37)       # it looks back at the office
DOOM_DOOR_SIZE  = (0.60, 6.3, 4.5)             # 3x the old 0.20 / 2.1 / 1.5
# THE TEXT ABOVE IT IS GONE. It used to hang the level title ("E1M1 :: HANGAR")
# over the door on a billboard. I wanted that off, so the label entity is
# kept - a dozen lines still enable and disable it - but it is never given any
# text and never switched on. See Game.open_door().
DOOM_DOOR_LABEL = False


def _door_yaw(from_pos, to_pos):
    d = to_pos - from_pos
    return math.degrees(math.atan2(d.x, d.z)) - 90


door_to_doom = Entity(parent=city_root, model='cube',
                      position=DOOM_DOOR_POS + Vec3(0, DOOM_DOOR_SIZE[1] / 2, 0),
                      scale=DOOM_DOOR_SIZE,
                      rotation_y=_door_yaw(DOOM_DOOR_POS, DOOM_DOOR_FACES),
                      texture=crunchy_texture(ASSETS / DOOM_FOLDER, 'BIGDOOR4'),
                      color=RGB(190, 120, 115), collider='box', unlit=True,
                      enabled=False)
door_to_doom.is_doom_door = True     # so E can find it - see do_interact()
print('DOOM door: %.1f x %.1fm at (%.2f, %.2f), floor on y=%.2f, top at y=%.2f, '
      'facing %.0f deg'
      % (DOOM_DOOR_SIZE[2], DOOM_DOOR_SIZE[1], DOOM_DOOR_POS.x, DOOM_DOOR_POS.z,
         DOOM_DOOR_POS.y, DOOM_DOOR_POS.y + DOOM_DOOR_SIZE[1],
         door_to_doom.rotation_y))
# The red pool that used to sit under the door is gone. This entity stays so
# every enable/disable line still has something to talk to, but it never draws.
# these two follow the door, so they move to city_root with it
door_glow = Entity(parent=city_root, model='quad', rotation_x=90,
                   position=DOOM_DOOR_POS + Vec3(0, 0.03, 0), scale=0.001,
                   color=color.clear, unlit=True, enabled=False)
door_label = Text('', parent=city_root, scale=6,
                  position=DOOM_DOOR_POS + Vec3(0, DOOM_DOOR_SIZE[1] + 0.5, 0),
                  billboard=True, color=RGB(230, 90, 80), enabled=False)
door_label.setFogOff(1)      # readable through the village fog

# the friend, for the finale only
try:
    friend = Entity(parent=office_root, position=FRIEND_POS, enabled=False)
    _fit = FRIEND_HEIGHT / FRIEND_MODEL_H
    if FRIEND_IS_OBJ:
        # Loaded through our own parser so the single texture sheet actually
        # lands on it - Ursina's .obj importer throws the .mtl away.
        _fobj = find_asset(f'{FRIEND_MODEL}.obj')
        _ftex = crunchy_texture(None, FRIEND_TEXTURE)
        # rotation_y 0, not 180. He was turned to face AWAY from you - you were
        # being shown his back through the whole confrontation.
        friend.body = Entity(parent=friend, scale=_fit, rotation_y=0)
        # bend_arms is NOT passed. FRIEND_ARM_DROP swings anything out past
        # the shoulder down to the hips - which is exactly the raised right
        # arm i posed him with, so applying it here would undo that. It
        # belonged to male_cheaple's T-pose and nothing else.
        for _mat, (_v, _u, _c) in load_obj_by_material(
                _fobj, flip_x=False, shade=True,
                pose=pose_friend_arm).items():
            if not _v:
                continue
            _mtex = crunchy_texture(None,
                                    FRIEND_TEXTURES.get(_mat, FRIEND_TEXTURE))
            Entity(parent=friend.body,
                   model=Mesh(vertices=_v, uvs=_u, colors=_c,
                              mode='triangle', static=True),
                   texture=_mtex,
                   color=color.white if _mtex else RGB(190, 180, 170),
                   double_sided=True, unlit=True)
    else:
        friend.body = Entity(parent=friend, model=FRIEND_MODEL,
                             scale=_fit, rotation_y=180)
    # A HITBOX YOU CANNOT MISS
    # shoot him and it registers right away."
    friend.collider = BoxCollider(friend,
                                  center=Vec3(0, FRIEND_HITBOX.y / 2, 0),
                                  size=FRIEND_HITBOX)
except Exception as e:
    print('friend model failed, using a stand-in:', e)
    friend = Entity(parent=office_root, model='cube', color=RGB(150, 150, 160),
                    position=FRIEND_POS + Vec3(0, 1, 0), scale=(0.7, 2, 0.5),
                    unlit=True, collider='box', enabled=False)


class FriendWatcher(Entity):
    def update(self):
        if game is None or game.state != 'finale' or not friend.enabled:
            return
        want = math.degrees(math.atan2(player.x - friend.x, player.z - friend.z))
        friend.rotation_y = lerp_angle(friend.rotation_y, want, min(1, time.dt * 3.5))

        # He's a static T-posed mesh, so the life has to be faked: breathing,
        # a slow weight shift from foot to foot, and an occasional small lean.
        # Enough that he reads as standing there rather than parked there.
        body = getattr(friend, 'body', None)
        if body is None:
            return
        t = time.time()
        breathe = math.sin(t * 1.3) * 0.010
        shift = math.sin(t * 0.42)
        body.y = breathe
        body.rotation_z = shift * 1.6            # weight onto one hip
        body.rotation_x = math.sin(t * 0.9) * 1.1
        body.x = shift * 0.012


def lerp_angle(a, b, t):
    diff = (b - a + 180) % 360 - 180
    return a + diff * t


friend_watcher = FriendWatcher()

# THE WALK-OUT DOOR IS IN THE ROOM, NOT BEHIND THE DESK
# The way out, for the finale only. It used to be a child of office_root at
# z = -5, which was fine when the desk stood in an open village. In a 7.5
# metre room, five metres behind a desk that is itself off-centre puts this
# door THROUGH THE BACK WALL - you would have been asked to walk out through
# solid geometry.
#
# It hangs off apartment_root now and sits right beside your own front door,
# which is better than it was anyway: the choice is to leave by the door you
# have always left by.
EXIT_DOOR_POS = Vec3(APARTMENT_DOOR_X - 2.6, 1.05,
                     -APARTMENT_SIZE[2] / 2 + 0.2)
exit_door = Entity(parent=apartment_root, model='cube', position=EXIT_DOOR_POS,
                   scale=(1.4, 2.1, 0.2), color=RGB(190, 185, 170),
                   collider='box', unlit=True, enabled=False)
exit_door.is_exit = True
exit_label = Text('', parent=apartment_root,
                  position=EXIT_DOOR_POS + Vec3(0, 1.5, 0),
                  scale=6, billboard=True, color=RGB(200, 200, 190), enabled=False)


# ==================================================================
# THE DOOM LEVEL - map, enemies, pickups
# ==================================================================
doom_root = Entity(enabled=False)
# The DOOM level is NOT built here. It is 1800 triangles of geometry plus 56
# textures, and building it at startup cost a noticeable chunk of the loading
# time and then left it sitting in memory through the whole office section.
# See prepare_doom() - it happens behind the title screen instead.
doom_collision, doom_pieces = None, []
# the sludge's own collider, built by build_doom_map. ToxicFloors
# raycasts against ONLY this, which is what makes the poison work at all.
toxic_collision = None
_doom_built = False


def ensure_doom_built():
    global doom_collision, doom_pieces, _doom_built
    if _doom_built:
        return doom_collision
    _doom_built = True
    started = time.time()
    doom_collision, doom_pieces = build_doom_map(doom_root)
    if doom_collision:
        print(f'DOOM level built in {time.time() - started:.1f}s')
    return doom_collision


def collect_floor_points():
    points = []
    if not doom_collision:
        return points
    verts = doom_collision.model.vertices
    seen = set()
    for i in range(0, len(verts) - 2, 3):
        a, b, c = verts[i], verts[i + 1], verts[i + 2]
        if abs(a[1] - b[1]) > 0.02 or abs(a[1] - c[1]) > 0.02:
            continue                                        # not horizontal
        centre = Vec3((a[0] + b[0] + c[0]) / 3, a[1], (a[2] + b[2] + c[2]) / 3)

        # don't keep 50 points in the same square metre
        key = (round(centre.x), round(centre.y), round(centre.z))
        if key in seen:
            continue
        seen.add(key)

        # headroom test: this is what separates floors from ceilings
        up = raycast(centre + Vec3(0, 0.2, 0), Vec3(0, 1, 0), distance=6,
                     ignore=nav_ignore())
        if not up.hit or up.distance < EYE_HEIGHT.get('doom', PLAYER_HEIGHT) + 0.1:
            continue
        points.append(centre)
    return points


# IMPORTANT: this list is built after the first frame is drawn, not here.
# Raycasts don't work until the game has rendered once, so doing it at startup
# silently returns nothing and every enemy ends up spawning in your face.
_FLOOR_POINTS = None
_REACHABLE = None
_ALL_SPOTS = None       # every standable spot the sampler found, roof excluded
_WALKABLE_CLEAN = None  # the same list minus the dead zones
_enemy_pool = None      # the dedicated enemy spawn points, per level


def walkable_spots():
    global _WALKABLE_CLEAN
    if _WALKABLE_CLEAN is not None:
        return _WALKABLE_CLEAN
    build_navigation()          # fills _ALL_SPOTS as a side effect also
    spots = _ALL_SPOTS or get_floor_points() or []
    if DOOM_DEAD_ZONES:
        keep = [p for p in spots if not in_dead_zone(p)]
        dropped = len(spots) - len(keep)
        if dropped:
            print('doom: %d walkable spots removed - they are inside the %d '
                  'blocked-off area(s), nothing spawns there now'
                  % (dropped, len(DOOM_DEAD_ZONES)))
        spots = keep
    _WALKABLE_CLEAN = spots
    return spots


def get_floor_points():
    global _FLOOR_POINTS
    if _FLOOR_POINTS is None:
        _FLOOR_POINTS = collect_floor_points()
        print(f'{len(_FLOOR_POINTS)} standable spots found')
    return _FLOOR_POINTS


def build_navigation():
    global _REACHABLE
    if _REACHABLE is not None:
        return _REACHABLE
    if not doom_collision:
        _REACHABLE = []
        return _REACHABLE

    started = time.time()
    verts = doom_collision.model.vertices
    min_x = min(v[0] for v in verts); max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts); max_y = max(v[1] for v in verts)
    min_z = min(v[2] for v in verts); max_z = max(v[2] for v in verts)

    # sample every column of the map, top to bottom
    # A single ray down only finds the roof, so we walk down through each
    # column collecting every surface: ground floor, walkways, ledges.
    #this idea i stole from a tutorial and pretty much copy pasted with my own numbers
    spots = []
    step = NAV_GRID_STEP
    x = min_x
    while x <= max_x:
        z = min_z
        while z <= max_z:
            y = max_y + 1.0
            for _ in range(8):
                down = raycast(Vec3(x, y, z), Vec3(0, -1, 0),
                               distance=(y - min_y) + 2, ignore=nav_ignore())
                if not down.hit:
                    break
                surface = down.world_point.y
                up = raycast(Vec3(x, surface + 0.15, z), Vec3(0, 1, 0),
                             distance=6, ignore=nav_ignore())
                if up.hit and up.distance >= EYE_HEIGHT.get('doom', PLAYER_HEIGHT) + 0.1:
                    spots.append(Vec3(x, surface, z))
                y = surface - 0.2
                if y < min_y:
                    break
            z += step
        x += step

    buckets = {}
    for i, p in enumerate(spots):
        buckets.setdefault((round(p.x / step), round(p.z / step)), []).append(i)

    links = {i: [] for i in range(len(spots))}
    for i, p in enumerate(spots):
        gx, gz = round(p.x / step), round(p.z / step)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0:
                    continue
                for j in buckets.get((gx + dx, gz + dz), ()):
                    if j <= i:
                        continue
                    q = spots[j]
                    if abs(q.y - p.y) > STEP_HEIGHT:
                        continue
                    a, b = p + Vec3(0, 0.5, 0), q + Vec3(0, 0.5, 0)
                    if not raycast(a, (b - a).normalized(),
                                   distance=distance(a, b), ignore=nav_ignore()).hit:
                        links[i].append(j)
                        links[j].append(i)

    if not spots:
        _REACHABLE = []
        return _REACHABLE
    start = min(range(len(spots)), key=lambda i: distance(spots[i], DOOM_SPAWN))
    seen = {start}
    queue = [start]
    while queue:
        node = queue.pop()
        for other in links[node]:
            if other not in seen:
                seen.add(other)
                queue.append(other)

    global _ALL_SPOTS
    _ALL_SPOTS = spots
    _REACHABLE = [spots[i] for i in seen]
    print(f'navigation: {len(spots)} standable spots sampled, {len(_REACHABLE)} '
          f'of them strictly reachable from spawn, in {time.time() - started:.1f}s')
    if len(_REACHABLE) < len(spots) * 0.4:
        print('   (the strict flood fill is pessimistic on this map - DOOM has '
              'lifts and stairs it cannot follow. Enemy spawns and the key and '
              'exit use the full sampled set instead; see walkable_spots.)')
    return _REACHABLE


class NavBuilder(Entity):
    def __init__(self):
        super().__init__()
        self.frames = 0

    def update(self):
        self.frames += 1
        if self.frames < 2:
            return
        # the office has to be on for the desk raycast to hit anything
        was_office = office_root.enabled
        office_root.enabled = True
        try:
            seat_phone_on_desk()
        finally:
            office_root.enabled = was_office

        #loads the doom level right at start up which is why the start up is pretty long but its better for overall experience
        prepare_doom()
        self.enabled = False


nav_builder = NavBuilder()      # seats the phone on the desk, frame 2


def warm_doom_sprites():
    started = time.time()
    n = 0
    for tier in ENEMY_TIERS.values():
        prefix = tier['sprite']
        for frame, angles in _sprite_index.get(prefix, {}).items():
            for stem, _flip in angles.values():
                if sprite_texture(stem) is not None:
                    n += 1
    print('DOOM sprites: %d frames pre-loaded in %.2fs (no stutter when they '
          'first appear)' % (n, time.time() - started))


def prepare_doom():
    ensure_doom_built()
    warm_doom_sprites()
    if doom_collision and _REACHABLE is None:
        was = doom_root.enabled
        doom_root.enabled = True
        try:
            get_floor_points()
            build_navigation()
            # The room survey is 8 rays per walkable spot - about 5,600 of
            # them - and it used to run the first time a level got populated,
            # which is exactly when you are watching. Done here it happens
            # behind the title screen with the rest of the loading.
            build_enemy_rooms()
        finally:
            doom_root.enabled = was


def snap_to_doom_floor(p, label='spawn'):
    eye = EYE_HEIGHT.get('doom', PLAYER_HEIGHT)
    surfaces = []
    y = max(p.y, 0.0) + 6.0
    for _ in range(14):
        down = raycast(Vec3(p.x, y, p.z), Vec3(0, -1, 0), distance=200,
                       ignore=nav_ignore())
        if not down.hit:
            break
        surf = down.world_point.y
        up = raycast(Vec3(p.x, surf + 0.2, p.z), Vec3(0, 1, 0), distance=8,
                     ignore=nav_ignore())
        if (not up.hit) or up.distance >= eye + 0.1:
            surfaces.append(surf)
        y = surf - 0.3
        if y < -60:
            break

    if surfaces:
        best = min(surfaces, key=lambda s: abs(s - 0.0))
        out = Vec3(p.x, best + 0.15, p.z)
        if abs(best - p.y) > 0.5:
            print('   DOOM %s: your y was %.2f, the real floor in that column '
                  'is %.2f (of %d surfaces found) - using the floor'
                  % (label, p.y, best, len(surfaces)))
        return out

    # no column data at all - fall back to the sampled walkable set, which also
    # excludes the roof, and say so
    snapped = nearest_walkable(Vec3(p.x, 0.0, p.z), fallback=p)
    print('   DOOM %s: nothing solid in that column - snapped to the nearest '
          'walkable spot %s instead'
          % (label, tuple(round(v, 1) for v in snapped)))
    return Vec3(snapped.x, snapped.y + 0.15, snapped.z)


def nearest_walkable(p, fallback=None):
    pool = walkable_spots()
    if not pool:
        return fallback if fallback is not None else p
    best, bd = None, 1e18
    for q in pool:
        d = (q.x - p.x) ** 2 + (q.y - p.y) ** 2 * 0.35 + (q.z - p.z) ** 2
        if d < bd:
            bd, best = d, q
    if best is None:
        return fallback if fallback is not None else p
    if math.sqrt(bd) > 0.75:
        print('   (snapped %s -> %s, %.1fm, so it is not in a wall)'
              % (tuple(round(v, 1) for v in p), tuple(round(v, 1) for v in best),
                 math.sqrt(bd)))
    return Vec3(best)


def enemy_spawn_pool():
    global _enemy_pool
    if _enemy_pool is not None:
        return _enemy_pool
    pool = walkable_spots()
    route = [DOOM_SPAWN, KEY_SPOT_FIRST] + KEY_SPOTS + EXIT_SPOTS + [EXIT_BIG_SPOT]
    ceiling = DOOM_SPAWN.y + ENEMY_MAX_HEIGHT
    good = [p for p in pool
            if p.y < ceiling
            and any(distance(Vec3(p.x, 0, p.z), Vec3(z.x, 0, z.z))
                    < ENEMY_ZONE_RADIUS for z in route)]
    # kept if it is at least ENEMY_SPAWN_SPACING from every point already
    # kept. That turns a few hundred floor samples into a few dozen deliberate
    good.sort(key=lambda p: (round(p.x, 2), round(p.z, 2), round(p.y, 2)))
    spaced = []
    gap2 = ENEMY_SPAWN_SPACING ** 2
    for p in good:
        if all((p.x - q.x) ** 2 + (p.z - q.z) ** 2 > gap2 for q in spaced):
            spaced.append(p)
    _enemy_pool = spaced or good or pool
    print('enemy spawn points: %d walkable spots on your route -> %d dedicated '
          'spawn points, %.0fm apart' % (len(good), len(_enemy_pool),
                                         ENEMY_SPAWN_SPACING))
    return _enemy_pool


def pick_spawn_point(near, min_dist=28, max_dist=75, avoid=()):
    pool = enemy_spawn_pool()
    candidates = [p for p in pool
                  if min_dist < distance(p, near) < max_dist
                  and abs(p.y - near.y) < 8]        # roughly the same storey
    if not candidates:      # nothing at that range - take anything on-route
        candidates = [p for p in pool if distance(p, near) > 8]
    random.shuffle(candidates)
    if avoid:
        # prefer somewhere well clear of the enemies already on the map
        candidates.sort(key=lambda p: -min([distance(p, a) for a in avoid] or [0]))
        candidates = candidates[:max(8, len(candidates) // 3)]
        random.shuffle(candidates)
    for p in candidates[:40]:
        eye = p + Vec3(0, 1.2, 0)
        target = near + Vec3(0, 1.2, 0)
        ray = raycast(eye, (target - eye).normalized(),
                      distance=distance(eye, target), ignore=nav_ignore())
        if not ray.hit:
            return p
    # nothing with clear sight? take any floor point at the right range
    if candidates:
        return random.choice(candidates)
    # LAST RESORT, and it refuses to give up and drop something in your lap.
    # It walks a ring at min_dist looking for real floor underneath; only if
    # the whole ring fails does it fall back, and even then it stays out at
    # min_dist rather than landing on top of you.
    for i in range(24):
        angle = i / 24 * math.tau
        guess = near + Vec3(math.cos(angle) * min_dist, 6,
                            math.sin(angle) * min_dist)
        down = raycast(guess, Vec3(0, -1, 0), distance=40, ignore=nav_ignore())
        if down.hit:
            # and there has to be headroom, or it's spawning inside geometry
            up = raycast(down.world_point + Vec3(0, 0.3, 0), Vec3(0, 1, 0),
                         distance=4, ignore=nav_ignore())
            if not up.hit or up.distance > 1.8:
                return down.world_point
    angle = random.uniform(0, math.tau)
    return near + Vec3(math.cos(angle) * min_dist, 0.2, math.sin(angle) * min_dist)


# Everything that decides WHERE an enemy stands. Nothing in here is typed in
# by hand: it is all measured off the level the same way the walkable spots, as most of the game is
_enemy_rooms = None        # [[Vec3, ...], ...] the spots in each room
_enemy_corridor = None     # [Vec3, ...]        every narrow spot


def space_width_at(p):
    eye = p + Vec3(0, 1.15, 0)
    reach = []
    for i in range(8):
        a = math.radians(i * 45)
        d = Vec3(math.sin(a), 0, math.cos(a))
        hit = raycast(eye, d, distance=ENEMY_ROOM_PROBE, ignore=nav_ignore())
        reach.append(hit.distance if hit.hit else ENEMY_ROOM_PROBE)
    return min(reach[i] + reach[i + 4] for i in range(4))


def build_enemy_rooms():
    global _enemy_rooms, _enemy_corridor
    if _enemy_rooms is not None:
        return _enemy_rooms, _enemy_corridor
    started = time.time()
    spots = [p for p in walkable_spots()
             if p.y < DOOM_SPAWN.y + ENEMY_MAX_HEIGHT]
    if not spots:
        print('!! no walkable spots - cannot work out any rooms') # failsafe thing
        _enemy_rooms, _enemy_corridor = [], []
        return _enemy_rooms, _enemy_corridor

    open_spots, tight_spots = [], []
    for p in spots:
        (open_spots if space_width_at(p) >= ENEMY_ROOM_WIDTH
         else tight_spots).append(p)

    # Union-find over the sampling grid: two open spots one grid step apart
    # and on the same storey are the same room. Same trick as the house
    step = NAV_GRID_STEP
    parent = list(range(len(open_spots)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    cells = {}
    for i, p in enumerate(open_spots):
        cells.setdefault((int(round(p.x / step)), int(round(p.z / step))),
                         []).append(i)
    for i, p in enumerate(open_spots):
        gx, gz = int(round(p.x / step)), int(round(p.z / step))
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in cells.get((gx + dx, gz + dz), ()):
                    if j <= i or abs(open_spots[j].y - p.y) > ENEMY_ROOM_STEP_Y:
                        continue
                    a, b = find(i), find(j)
                    if a != b:
                        parent[b] = a

    blobs = {}
    for i in range(len(open_spots)):
        blobs.setdefault(find(i), []).append(open_spots[i])
    rooms = sorted(blobs.values(), key=len, reverse=True)
    small = [r for r in rooms if len(r) < ENEMY_ROOM_MIN_SPOTS]
    rooms = [r for r in rooms if len(r) >= ENEMY_ROOM_MIN_SPOTS][:ENEMY_ROOM_MAX]
    # a blob too small to be a room is still somewhere to stand: it goes in
    # with the corridors rather than being thrown away
    corridor = tight_spots + [p for r in small for p in r]

    _enemy_rooms, _enemy_corridor = rooms, corridor
    print('enemy rooms: %d rooms found (%s spots each) + %d corridor spots, '
          'from %d walkable, in %.1fs'
          % (len(rooms), '/'.join(str(len(r)) for r in rooms), len(corridor),
             len(spots), time.time() - started))
    for n, r in enumerate(rooms):
        cx = sum(p.x for p in r) / len(r)
        cz = sum(p.z for p in r) / len(r)
        cy = sum(p.y for p in r) / len(r)
        print('   room %d: %3d spots, centred (%6.1f, %5.1f, %6.1f)'
              % (n + 1, len(r), cx, cy, cz))
    return _enemy_rooms, _enemy_corridor


def spread_points(spots, count, min_gap):
    if not spots or count <= 0:
        return []
    cx = sum(p.x for p in spots) / len(spots)
    cz = sum(p.z for p in spots) / len(spots)
    pool = sorted(spots, key=lambda p: (round(p.x, 2), round(p.z, 2)))
    chosen = [min(pool, key=lambda p: (p.x - cx) ** 2 + (p.z - cz) ** 2)]
    while len(chosen) < count:
        best, best_d = None, -1.0
        for p in pool:
            d = min((p.x - q.x) ** 2 + (p.z - q.z) ** 2 for q in chosen)
            if d > best_d:
                best, best_d = p, d
        if best is None or best_d < min_gap * min_gap:
            break                      # the room is full, stop crowding it
        chosen.append(best)
    return chosen


_post_cache = {}


def enemy_posts(per_room, corridors):
    key = (per_room, corridors)
    if key in _post_cache:
        return _post_cache[key]
    rooms, corridor = build_enemy_rooms()
    posts = []
    # the arrival room is cleared out first, so nothing is standing
    # there when you land - see ENEMY_POST_MIN_FROM_SPAWN.
    quiet = ENEMY_POST_MIN_FROM_SPAWN

    def far_enough(p):
        return math.hypot(p.x - DOOM_SPAWN.x, p.z - DOOM_SPAWN.z) > quiet

    for r in rooms:
        usable = [p for p in r if far_enough(p)] or []
        for p in spread_points(usable, per_room, ENEMY_POST_SPACING):
            posts.append((Vec3(p), 'room'))
    for p in spread_points([p for p in corridor if far_enough(p)],
                           corridors, ENEMY_POST_SPACING * 1.6):
        posts.append((Vec3(p), 'corridor'))
    # AND EXTRA ONES AROUND THE BOSS
    # Anything within BOSS_CROWD_RADIUS of where he comes in gets considered,
    # and the spread picks BOSS_CROWD of them - so his end of the map is where
    # the fighting is, and the rest of the level is thinner than it was.
    near_boss = [p for p in (rooms and [q for r in rooms for q in r] or [])
                 + list(corridor)
                 if math.hypot(p.x - BOSS_SPAWN.x, p.z - BOSS_SPAWN.z)
                 < BOSS_CROWD_RADIUS and far_enough(p)]
    for p in spread_points(near_boss, BOSS_CROWD, ENEMY_POST_SPACING):
        posts.append((Vec3(p), 'room'))
    _post_cache[key] = posts
    return posts


_ignore_stamp, _ignore_cached = -1.0, ()


def shot_ignore():
    global _ignore_stamp, _ignore_cached
    now = time.time()
    if now - _ignore_stamp < 0.05:
        return _ignore_cached
    live = tuple(e for e in (game.enemies if game else ()) if e)
    _ignore_cached = live + tuple(doom_bounds_boxes)
    _ignore_stamp = now
    return _ignore_cached


def alert_enemies_near(point, radius):
    if game is None or game.state != 'doom':
        return 0
    woken = 0
    for e in list(game.enemies):
        if e.dying or e.awake:
            continue
        if distance(e.world_position, point) < radius:
            e.wake(spread=False)
            woken += 1
    return woken


def point_to_segment(p, a, b):
    ab = b - a
    length2 = ab.x * ab.x + ab.y * ab.y + ab.z * ab.z
    if length2 < 1e-9:
        return distance(p, a)
    ap = p - a
    t = (ap.x * ab.x + ap.y * ab.y + ap.z * ab.z) / length2
    t = clamp(t, 0.0, 1.0)
    return distance(p, a + ab * t)

class Fireball(Entity):
    def __init__(self, position, direction, damage, speed=None):
        super().__init__(model=gun_mesh('bullet'),
                         texture=crunchy_texture(WEAPON_ASSETS, WEAPON_TEXTURE),
                         position=position, scale=0.13,
                         # BRIGHT RED and half again as big, because
                         # the old amber at 0.09 was invisible against DOOM's
                         # brown walls and you could not see what was coming

                         color=RGB(255, 30, 20), unlit=True,
                         parent=doom_root)
        self.look_at(position + direction)
        self.direction = direction
        self.damage = damage
        self.speed = speed if speed else ENEMY_PROJECTILE_SPEED
        self.life = 6
        if game is not None:
            game.fireballs.append(self)      # so they can be counted

    def gone(self):
        if game is not None and self in game.fireballs:
            game.fireballs.remove(self)
        destroy(self)

    def puff(self):
        return

    def update(self):
        if game.state != 'doom':
            self.gone()
            return
        start = Vec3(self.world_position)
        end = start + self.direction * self.speed * time.dt

        # you first, and against the whole segment - see the docstring
        centre = player_pos() + Vec3(0, movement.eye * 0.55, 0)
        if point_to_segment(centre, start, end) < ENEMY_PROJECTILE_HIT:
            hurt_player(self.damage)
            self.gone()
            return

        # then the level. Other monsters are ignored unless you turn
        # ENEMY_FRIENDLY_FIRE on: with thirty of them in a room, shots that
        # stop on each other never reach you at all.
        ignore = (self, player)
        if not ENEMY_FRIENDLY_FIRE:
            ignore = ignore + shot_ignore()
        if raycast(start, self.direction,
                   distance=(end - start).length() + 0.25, ignore=ignore).hit:
            self.gone()
            return

        self.position = end
        self.life -= time.dt
        if self.life <= 0:
            self.gone()


class DoomEnemy(Entity):
    # frame letters, by state. DOOM's convention: A-D walk, E-G attack,
    # H onwards die. Anything the sprite set doesn't have gets dropped.
    WALK   = 'ABCD'
    FIRE   = 'EFG'
    DEATH  = 'HIJKL'

    # The eight directions a DOOM monster is allowed to walk in, as Ursina
    # yaws - 0 is +z, 90 is +x. Movement never uses anything else, which is
    # what stops the drifting, sliding, re-aiming-every-frame look.
    DIRS = (0, 45, 90, 135, 180, 225, 270, 315)
    DIAGS = {(90, 0): 45, (90, 180): 135, (270, 180): 225, (270, 0): 315}

    def __init__(self, position, tier, toughness=1.0, post=None, kind='room'):
        spec = ENEMY_TIERS[tier]
        self.spec = spec
        prefix = spec['sprite']
        # Height straight off the sprite: DOOM draws one pixel per map unit and
        # the player is 56 units, so the art decides how big it stands.
        px = sprite_pixel_height(prefix)
        want = (px / SPRITE_PX) * movement.eye
        if tier == 'boss':
            want *= BOSS_SIZE_MULT
        super().__init__(parent=doom_root, position=position)
        # The sprite hangs off a child quad so the parent can carry the collider
        # and the walking, while the child does the facing and the flinching.
        self.body = Entity(parent=self, model='quad', double_sided=True,
                           unlit=True, color=spec['tint'],
                           scale=(want * 0.82, want, 1), y=want / 2,
                           billboard=True)
        self.prefix = prefix
        self.walk_frames  = sprite_frames_present(prefix, self.WALK)
        self.fire_frames  = sprite_frames_present(prefix, self.FIRE)
        self.death_frames = sprite_frames_present(prefix, self.DEATH)
        # THE BOSS'S COLLIDER IS KEPT TO A NORMAL ENEMY'S FOOTPRINT.
        # He is drawn three times the size and he takes the same damage in the
        # same places, but he does not need a three-metre-wide box to walk
        # through a doorway with - that box was most of why he kept wedging.
        foot = spec['width'] * movement.eye * 0.55
        if tier == 'boss':
            foot = min(foot, spec['width'] * movement.eye * 0.55 / BOSS_SIZE_MULT * 1.6)
        self.collider = BoxCollider(self, center=Vec3(0, want / 2, 0),
                                    size=Vec3(foot, want, foot))
        self.tier = tier
        self.base_tint = spec['tint']
        self.height = want
        self.hp = spec['hp'] * toughness
        self.max_hp = self.hp
        # tier speeds are ratios of the player's, capped so nothing outruns you
        self.walk_speed = DOOM_SPEED * min(spec['speed'] / 4.0, ENEMY_SPEED_CAP)
        self.damage = spec['damage'] * toughness
        self.ranged = spec['ranged']
        self.cadence = spec.get('cadence', 1.8)
        self.is_enemy = True
        self.dying = False
        # True if the LEVEL killed it rather than you - see take_damage()
        self.killed_by_level = False
        # HE CANNOT BE HURT BY THE LEVEL
        # He walked into the nukage and killed himself, which handed me the
        # ending by accident in the least satisfying way possible. Anything
        # with this flag gets skipped by ToxicFloors - it is a hazard
        # immunity, not a damage immunity, so rockets still work as they did.
        self.is_boss = (tier == 'boss')
        self.hazard_proof = self.is_boss

        # ITS POST, AND WHETHER IT HAS NOTICED YOU
        self.post = Vec3(post) if post is not None else Vec3(position)
        self.post_kind = kind
        self.awake = False
        self.state = 'idle'
        self.state_left = 0.0
        self.attack_cooldown = random.uniform(*ENEMY_REACTION)
        self.target_seen = False
        self.last_seen = None          # where you were when it last saw you
        self.forget = 0.0
        # staggered, so forty enemies never fire their sight rays on the same
        # frame - this is most of why forty of them costs what four used to
        self.los_timer = random.uniform(0, ENEMY_LOS_TICK)

        # walking
        self.movedir = None            # one of DIRS, or None for "boxed in"
        self.dir_timer = 0.0
        self.rethink_cool = 0.0
        self.stuck_timer = 0.0

        # animation state
        self.anim_t = random.uniform(0, 10)     # offset so they're out of step
        self.heading = random.choice(self.DIRS)  # the way it is facing
        self.frame_now = ''
        self._flip = False

        # THE NAME OVER ITS HEAD, for a few seconds.
        # The boss always gets his name; everybody else only if they are close
        # enough for you to read it, which saves fifty text meshes being built
        # in the frame the level starts.
        # ENEMY_NAME_TAGS is the switch for this - see the long note next to
        # it in SECTION 1. False means no Text gets built at all, which is the
        # point: it was the BUILDING of them that i could see.
        ### Me checking in after game is done, the boss name lowk isnt really visable
        _near = (ENEMY_NAME_TAGS
                 and (tier == 'boss'
                      or distance(Vec3(position), player.world_position)
                      < NAME_SHOW_DISTANCE))
        self.name_tag = Text(BOSS_NAME if tier == 'boss'
                             else random.choice(ENEMY_NAMES),
                             parent=self, billboard=True, origin=(0, 0),
                             y=want * 1.12, scale=11 if tier == 'boss' else 7,
                             color=RGB(255, 235, 120) if tier == 'boss'
                             else RGB(230, 230, 235)) if _near else None
        self.name_left = NAME_SHOW_SECONDS if _near else 0.0

    # drawing
    def view_angle(self):
        to_cam = camera.world_position - self.world_position
        bearing = math.degrees(math.atan2(to_cam.x, to_cam.z))
        rel = (bearing - self.heading) % 360
        return int((rel + 22.5) % 360 // 45) + 1

    def set_frame(self, letter):
        stem, flip = sprite_frame(self.prefix, letter, self.view_angle())
        if not stem:
            return
        # THE WHOLE POINT OF THIS `if` IS THAT NOTHING HAPPENS MOST FRAMES.
        # An enemy shows the same sprite for several frames in a row, so the
        # texture and the width only need setting when the frame actually
        # changes. Writing scale_x every frame - which is what the last line
        # used to do, outside this guard - is a transform update on the scene
        # graph, times forty enemies, times sixty frames a second, to set it
        # to the value it already had.
        if stem != self.frame_now or flip != self._flip:
            tex = sprite_texture(stem)
            if tex:
                self.body.texture = tex
                # a sprite is only as wide as its own art, so keep the aspect
                width = (abs(self.body.scale_y) * tex.width
                         / max(1, tex.height))
                # negative scale_x mirrors the quad - that is how DOOM packs
                # the diagonal angles, one image used for both sides
                self.body.scale_x = -width if flip else width
            self.frame_now, self._flip = stem, flip

    def animate_body(self, moving, dist):
        if self.state == 'die':
            self.state_left -= time.dt
            i = min(len(self.death_frames) - 1,
                    int((1 - max(0, self.state_left) / self.death_time)
                        * len(self.death_frames)))
            self.set_frame(self.death_frames[i])
            if self.state_left <= 0:
                self.finish_death()
            return True
        if self.state == 'fire':
            self.state_left -= time.dt
            i = min(len(self.fire_frames) - 1,
                    int((1 - self.state_left / self.fire_time) * len(self.fire_frames)))
            self.set_frame(self.fire_frames[i])
            if self.state_left <= 0:
                self.state = 'hunt' if self.awake else 'idle'
            return True
        # walking: cycle A-B-C-D. A standing enemy holds frame A.
        if moving:
            self.anim_t += time.dt * (4.0 + self.walk_speed)
            self.set_frame(self.walk_frames[int(self.anim_t) % len(self.walk_frames)])
        else:
            self.set_frame(self.walk_frames[0])
        return False

    def face_player(self):
        d = player_pos() - self.world_position
        self.rotation_y = math.degrees(math.atan2(d.x, d.z))

    def flash(self):
        self.body.color = RGB(255, 110, 110)
        invoke(setattr, self.body, 'color', self.base_tint, delay=0.07)

    # damage and dying
    def take_damage(self, amount, by_player=True):
        if self.dying:
            return
        if not by_player:
            self.killed_by_level = True
        self.hp -= amount
        self.flash()
        # being shot at is the loudest thing that can happen to you. DOOM
        # wakes the monster AND makes it target whoever hurt it; there is only
        # one thing that can hurt it here, so it just wakes up angry.
        if not self.awake:
            self.wake()
        else:
            self.last_seen = Vec3(player_pos())
            self.forget = ENEMY_FORGET
        if self.hp <= 0:
            self.die()

    def die(self):
        if self.dying:
            return
        self.dying = True
        self.collider = None
        self.is_enemy = False
        self.awake = False
        self.state = 'die'
        self.death_time = self.state_left = 0.10 * len(self.death_frames)
        beep(pitch=-24, length=0.3, wave='noise', volume=0.4)
        clip = doom_sound('death') or gun_sound('destroyed')
        if clip:
            clip.play()
        game.enemy_died(self)

    def finish_death(self):
        destroy(self)

    # noticing you  (DOOM's A_Look)
    def can_see_player(self):
        eye = self.world_position + Vec3(0, self.height * 0.62, 0)
        target = player_pos() + Vec3(0, movement.eye * 0.6, 0)
        gap = target - eye
        d = gap.length()
        if d < 0.2:
            return True
        hit = raycast(eye, gap.normalized(), distance=d,
                      ignore=shot_ignore() + (self,))
        return (not hit.hit) or hit.entity == player

    def look_for_player(self):
        gap = player_pos() - self.world_position
        flat = math.hypot(gap.x, gap.z)
        if flat > ENEMY_SIGHT:
            return False
        # NOTHING STARTS while you are still in the room you arrived in.

        if (ENEMY_QUIET_RADIUS > 0
                and math.hypot(player.x - DOOM_SPAWN.x,
                               player.z - DOOM_SPAWN.z) < ENEMY_QUIET_RADIUS):
            return False
        if flat <= ENEMY_HEARING:
            return True                 # too close to need to see you
        if ENEMY_SIGHT_ARC < 360:
            bearing = math.degrees(math.atan2(gap.x, gap.z))
            if abs((bearing - self.heading + 180) % 360 - 180) > ENEMY_SIGHT_ARC / 2:
                return False
        return self.can_see_player()

    def wake(self, spread=True):
        if self.awake or self.dying:
            return
        self.awake = True
        self.state = 'hunt'
        self.target_seen = True
        self.last_seen = Vec3(player_pos())
        self.forget = ENEMY_FORGET
        # deliberately short
        self.attack_cooldown = random.uniform(*ENEMY_REACTION)
        if random.random() < 0.25:
            clip = doom_sound('sight')
            if clip:
                clip.play()
        if spread and ENEMY_ALERT_SPREAD > 0:
            here = self.world_position
            for other in game.enemies:
                if (other is not self and not other.awake and not other.dying
                        and distance(other.world_position, here) < ENEMY_ALERT_SPREAD):
                    other.wake(spread=False)

    # shooting
    def bearing_to_player(self):
        gap = player_pos() - self.world_position
        return math.degrees(math.atan2(gap.x, gap.z))

    def start_fire(self):
        self.state = 'fire'
        self.movedir = None                       # it plants its feet
        # and it is looking straight at you while it does it, so the sprite
        # shows you its front rather than whichever way it last walked
        self.heading = self.bearing_to_player()
        self.aim_at = Vec3(player_pos())  # <- the snapshot
        self.fire_time = self.state_left = 0.14 * len(self.fire_frames)
        invoke(self.release_shot, delay=self.fire_time * 0.55)
        clip = doom_sound('enemy_fire')
        if clip:
            clip.play()

    def release_shot(self):
        if self.dying or game.state != 'doom' or not player.enabled:
            return
        target = getattr(self, 'aim_at', None)
        if target is None or not ENEMY_AIM_LAST_POS:
            target = Vec3(player_pos())
        if ENEMY_AIM_JITTER:
            target = target + Vec3(random.uniform(-1, 1) * ENEMY_AIM_JITTER, 0,
                                   random.uniform(-1, 1) * ENEMY_AIM_JITTER)
        aim = (target + Vec3(0, movement.eye * 0.55, 0) - self.world_position
               - Vec3(0, self.height * 0.6, 0))
        if aim.length() < 0.01:
            return
        # do not add to a screen that is already full of them
        if len(game.fireballs) >= ENEMY_MAX_PROJECTILES:
            return
        Fireball(self.world_position + Vec3(0, self.height * 0.6, 0),
                 aim.normalized(), self.damage)

    def swing(self):
        hurt_player(self.damage)
        if self.fire_frames:
            self.state = 'fire'
            self.movedir = None
            self.fire_time = self.state_left = 0.14 * len(self.fire_frames)
        clip = doom_sound('enemy_melee')
        if clip:
            clip.play()
        self.attack_cooldown = max(0.6, self.cadence * 0.5)

    # walking  (DOOM's P_NewChaseDir, more or less line for line)
    @staticmethod
    def dir_vector(yaw):
        a = math.radians(yaw)
        return Vec3(math.sin(a), 0, math.cos(a))

    def try_walk(self, yaw):
        d = self.dir_vector(yaw)
        # THE BOSS FITS WHERE THE LITTLE ONES FIT
        # He gets tested at a NORMAL enemy's
        # chest height instead, so if a shambler can get through a gap, so can
        # he. Nothing about how big he looks changes.
        probe_h = min(self.height, movement.eye) * 0.62
        eye = self.world_position + Vec3(0, probe_h, 0)
        hit = raycast(eye, d, distance=ENEMY_TRY_WALK, ignore=(self, player))
        if hit.hit:
            return False
        ahead = self.world_position + d * ENEMY_TRY_WALK
        down = raycast(ahead + Vec3(0, ENEMY_STEP_UP, 0), Vec3(0, -1, 0),
                       distance=ENEMY_STEP_UP + ENEMY_DROP_MAX,
                       ignore=nav_ignore() + (self,))
        if not down.hit:
            return False
        return (down.world_point.y - self.y) <= ENEMY_STEP_UP

    def new_chase_dir(self, target):
        if self.rethink_cool > 0:
            return
        self.rethink_cool = 0.12
        dx = target.x - self.x
        dz = target.z - self.z
        old = self.movedir
        turn = None if old is None else (old + 180) % 360
        EPS = 1.2

        def take(yaw):
            self.movedir = yaw
            self.dir_timer = random.uniform(*ENEMY_DIR_RETHINK)
            self.heading = yaw
            return True

        dirx = 90 if dx > EPS else (270 if dx < -EPS else None)
        dirz = 0 if dz > EPS else (180 if dz < -EPS else None)

        if dirx is not None and dirz is not None:
            diag = self.DIAGS[(dirx, dirz)]
            if diag != turn and self.try_walk(diag):
                return take(diag)

        first, second = dirx, dirz
        if abs(dz) > abs(dx) or random.random() > 0.78:
            first, second = dirz, dirx
        for cand in (first, second):
            if cand is None or cand == turn:
                continue
            if self.try_walk(cand):
                return take(cand)

        if old is not None and self.try_walk(old):
            return take(old)

        order = list(self.DIRS)
        if random.getrandbits(1):
            order.reverse()
        for cand in order:
            if cand != turn and self.try_walk(cand):
                return take(cand)

        if turn is not None and self.try_walk(turn):
            return take(turn)
        self.movedir = None          # genuinely boxed in

    def walk_toward(self, target):
        self.dir_timer -= time.dt
        self.rethink_cool -= time.dt
        if self.movedir is None or self.dir_timer <= 0:
            self.new_chase_dir(target)
        if self.movedir is None:
            self.stuck_timer += time.dt
            return False
        d = self.dir_vector(self.movedir)
        step = self.walk_speed * time.dt
        # same as try_walk - a normal chest height, so the boss does
        # not snag on anything a small sprite clears
        eye = self.world_position + Vec3(
            0, min(self.height, movement.eye) * 0.62, 0)
        blocked = raycast(eye, d, distance=step + 0.45, ignore=(self, player))
        if blocked.hit:
            self.stuck_timer += time.dt
            self.dir_timer = 0
            self.new_chase_dir(target)
            return False
        self.position += d * step
        self.heading = self.movedir
        self.stuck_timer = max(0.0, self.stuck_timer - time.dt)
        self.settle_on_floor()
        return True

    def settle_on_floor(self):
        ground = raycast(self.world_position + Vec3(0, ENEMY_STEP_UP, 0),
                         Vec3(0, -1, 0), distance=40,
                         ignore=nav_ignore() + (self,))
        if ground.hit:
            climb = ground.world_point.y - self.y
            if climb <= ENEMY_STEP_UP:
                rate = 12 if climb > 0 else 25
                want_y = lerp(self.y, ground.world_point.y,
                              min(1, time.dt * rate))
                # and a hard clamp: whatever the lerp asks for, nothing rises
                # more than one step in a single frame, ever
                self.y = min(want_y, self.y + ENEMY_STEP_UP)
        else:
            self.y -= ENEMY_FALL_SPEED * time.dt

    # the frame
    def update(self):
        if game.state != 'doom' or not player.enabled:
            return
        if self.name_left > 0:
            self.name_left -= time.dt
            if self.name_left <= 0 and self.name_tag:
                destroy(self.name_tag)
                self.name_tag = None

        # player_pos() instead of player.world_position. A level has up to
        # sixty of these and every one of them used to walk the scene graph to
        # ask the same question; now it gets answered once a frame for all of
        # them. Identical number, identical behaviour, much cheaper.
        gap = player_pos() - self.world_position
        dist = math.hypot(gap.x, gap.z)      # HORIZONTAL. A staircase must not
                                             # push you out of its reach.

        # dying
        if self.dying:
            self.animate_body(False, dist)
            return

        # FAR-OFF SLEEPERS COST ALMOST NOTHING
        # A level has up to sixty of these. animate_body() runs view_angle(),
        # which is an atan2 and a texture comparison, for every one of them
        # every frame - including the forty that are asleep on the other side
        # of the map and not even on screen. Past ENEMY_ANIM_DISTANCE the
        # animation gets skipped entirely and only the sight timer keeps
        # running, which is one raycast every fifth of a second.
        _far = dist > ENEMY_ANIM_DISTANCE

        # STANDING ON ITS POST, waiting for you.
        # Cheap on purpose: one raycast every fifth of a second, staggered,
        # and nothing else at all. Thirty dormant enemies cost about what one
        # active one does.
        if not self.awake:
            if not _far:
                self.animate_body(False, dist)
            self.los_timer -= time.dt
            if self.los_timer <= 0:
                self.los_timer = ENEMY_LOS_TICK * random.uniform(0.8, 1.4)
                if self.look_for_player():
                    self.wake()
            return

        # awake: it is looking at you from here on, whatever happens
        self.face_player()
        self.attack_cooldown -= time.dt
        self.los_timer -= time.dt
        if self.los_timer <= 0:
            self.los_timer = ENEMY_LOS_TICK * random.uniform(0.8, 1.3)
            self.target_seen = self.can_see_player()
            if self.target_seen:
                self.last_seen = Vec3(player_pos())
                self.forget = ENEMY_FORGET
        if not self.target_seen:
            self.forget -= time.dt
            if self.forget <= 0:
                # it has not seen you in a long time - walk to your actual
                # position anyway. It never gives up, it just stops pretending
                # it does not know where you are.
                self.last_seen = Vec3(player_pos())
                self.forget = ENEMY_FORGET

        # animate first: while it is shooting or dying it is PLANTED and
        # nothing below this line is allowed to happen.
        moving_now = (self.state == 'hunt' and self.movedir is not None
                      and dist > ENEMY_MELEE * 0.8)
        if self.animate_body(moving_now, dist):
            return
        if dist > ENEMY_AGGRO:
            return

        # hit you
        if dist < ENEMY_MELEE and self.attack_cooldown <= 0:
            self.swing()
            return

        # or shoot you, at where you were
        if (self.ranged and dist > ENEMY_FIRE_MIN and self.attack_cooldown <= 0
                and self.target_seen):
            self.start_fire()
            self.attack_cooldown = self.cadence
            return

        # walk
        # A ranged enemy that can see you and is already in range STANDS ITS
        # GROUND and shoots from there, which is what i wanted and what
        # DOOM does. Everything else closes in.
        hold = (self.ranged and ENEMY_STAND_AND_SHOOT and self.target_seen
                and dist <= ENEMY_ADVANCE_RANGE)
        if hold or (not self.ranged and dist < ENEMY_MELEE * 0.85):
            self.movedir = None
            self.heading = self.bearing_to_player()
            return
        target = (player_pos() if self.target_seen
                  else (self.last_seen or player_pos()))
        self.walk_toward(target)

        # IF IT EVER GETS SOMEWHERE IT SHOULD NOT BE, IT GOES BACK.
        # To its own post, not a random spot next to you: teleporting a
        # monster into your face is exactly the kind of thing that made the
        # old lot feel arbitrary.
        if self.y > DOOM_SPAWN.y + ENEMY_MAX_HEIGHT or self.y < -40:
            self.position = Vec3(self.post)
            self.movedir = None
            self.stuck_timer = 0
        elif self.stuck_timer > 9:
            self.position = Vec3(self.post)
            self.movedir = None
            self.stuck_timer = 0


class KeyPickup(Entity):
    def __init__(self, position):
        super().__init__(
            parent=doom_root,
            model='cube',
            texture=crunchy_texture(ASSETS / DOOM_FOLDER, KEY_TEXTURE),
            color=RGB(255, 80, 80),
            scale=(0.45, 0.62, 0.10),
            position=position + Vec3(0, 1.0, 0),
            unlit=True,
        )
        self.base_y = self.y
        # no red disc on the floor - the key is red enough on its own
        self.halo = Entity(parent=doom_root, scale=0.001, visible=False)
        self.label = Text('KEY', parent=doom_root, billboard=True, scale=9,
                          position=position + Vec3(0, 1.9, 0), color=RGB(255, 120, 120))

    def update(self):
        if game.state != 'doom':
            return
        self.rotation_y += 60 * time.dt
        self.y = self.base_y + math.sin(time.time() * 2.2) * 0.10
        if distance(player_pos(), self.world_position) < KEY_PICKUP_RANGE:
            game.take_key()
            game.key = None          # same dangling-reference trap as the guns
            destroy(self.halo)
            destroy(self.label)
            destroy(self)


class HealthPack(Entity):
    def __init__(self, position):
        tex = crunchy_texture(None, HEALTH_TEXTURE)
        if tex is None:
            for name in HEALTH_FALLBACKS:
                tex = crunchy_texture(None, name)
                if tex is not None:
                    break
        super().__init__(
            parent=doom_root,
            model='cube',
            texture=tex,
            color=color.white if tex else RGB(190, 40, 50),
            scale=HEALTH_SIZE,
            position=position + Vec3(0, 0.28, 0),
            unlit=True,
        )
        self.base_y = self.y
        self.label = Text(HEALTH_LABEL, parent=doom_root, billboard=True,
                          scale=7, position=position + Vec3(0, 0.95, 0),
                          color=RGB(255, 120, 130))

    def update(self):
        if game.state != 'doom':
            return
        self.rotation_y += 45 * time.dt
        self.y = self.base_y + math.sin(time.time() * 2.4) * 0.06
        if distance(player_pos(), self.world_position) < HEALTH_RANGE:
            if player.health >= PLAYER_MAX_HP:
                return                      # full up - leave it for later
            player.health = min(PLAYER_MAX_HP, player.health + HEALTH_AMOUNT)
            refresh_health()
            beep(pitch=6, length=0.18, wave='sine', volume=0.45)
            clip = doom_sound('pickup')
            if clip:
                clip.play()
            flash_title('+%d  %s' % (HEALTH_AMOUNT, HEALTH_LABEL), 1.2)
            if self in game.health_packs:
                game.health_packs.remove(self)
            destroy(self.label)
            destroy(self)


class ExitDoor(Entity):
    def __init__(self, position, size=(2.6, 2.7, 0.35), yaw=0):
        # The collider is part of the entity, so rotating the entity rotates
        # what you bump into as well - there is no second thing to keep in
        # step. The sign gets the same yaw so it stays flat on the door
        # rather than sticking out sideways above it.
        w, h, t = size
        lift = h / 2 if EXIT_DOOR_DROP else h / 2 + 1.35
        self.yaw = yaw
        super().__init__(
            parent=doom_root,
            model='cube',
            texture=crunchy_texture(ASSETS / DOOM_FOLDER, EXIT_TEXTURE),
            scale=size,
            position=position + Vec3(0, lift, 0),
            rotation=(0, yaw, 0),
            color=RGB(120, 120, 120),      # dim until you have the key
            unlit=True,
            collider='box',
        )
        # the sign sits just under the top of whatever size door this is,
        # rather than at a fixed height that only suited the small one
        self.sign = Entity(parent=doom_root, model='cube',
                           texture=crunchy_texture(ASSETS / DOOM_FOLDER, EXIT_SIGN),
                           scale=(min(1.7, w * 0.65), 0.5, 0.1),
                           position=position + Vec3(0, h + 0.35, 0),
                           rotation=(0, yaw, 0),
                           color=RGB(120, 120, 120), unlit=True)
        self.glow = Entity(parent=doom_root, scale=0.001, visible=False)
        self.open = False

    def unlock(self):
        self.open = True
        self.color = color.white
        self.sign.color = color.white

    def update(self):
        if game.state != 'doom' or not self.open:
            return
        if distance(player.world_position, self.world_position) < EXIT_RANGE:
            game.finish_level()


class ToxicFloors(Entity):
    def __init__(self):
        super().__init__()
        self.tick = 0.0

    @staticmethod
    def standing_in_sludge(pos):
        if toxic_collision is None:
            down = raycast(pos + Vec3(0, 0.45, 0), Vec3(0, -1, 0),
                           distance=1.2, ignore=(player,))
            return bool(down.hit and getattr(down.entity, 'is_toxic', False))
        down = raycast(pos + Vec3(0, 0.45, 0), Vec3(0, -1, 0),
                       distance=1.2, ignore=(player,),
                       traverse_target=toxic_collision)
        return bool(down.hit)

    def update(self):
        if game is None or game.state != 'doom' or not player.enabled:
            return
        self.tick -= time.dt
        if self.tick > 0:
            return
        self.tick = TOXIC_TICK
        if self.standing_in_sludge(player_pos()):
            hurt_player(TOXIC_DPS)
            flash_title('BURNING', 0.6)
        for e in list(game.enemies):
            # The boss is hazard-proof. He walked into the burning pit and
            # died in it, which handed me the ending for nothing - and it is
            # not a fight that should be losable to a puddle. Everything else
            # still burns exactly as before, including anything chasing you in.
            #important thing is that it will not always count for the livers count to get the best ending.
            if getattr(e, 'hazard_proof', False):
                continue
            if not e.dying and self.standing_in_sludge(e.world_position):
                # by_player=False: the sludge did this, not you. See
                # take_damage() and Game.enemy_died().
                e.take_damage(TOXIC_DPS, by_player=False)


toxic_floors = ToxicFloors()


class DoorOpener(Entity):
    def update(self):
        if game is None or game.state != 'doom' or not doors:
            return
        here = player.world_position
        for d in doors:
            near = distance(Vec3(d.centre.x, 0, d.centre.z),
                            Vec3(here.x, 0, here.z)) < DOOR_OPEN_RANGE
            want = d.rest_y + (DOOR_LIFT if near else 0.0)
            if abs(d.y - want) > 0.005:
                d.y = lerp(d.y, want, min(1, time.dt * DOOR_SPEED))


door_opener = DoorOpener()


def hurt_player(amount):
    if game.state not in ('doom', 'finale') or GODMODE:
        return
    player.health -= amount
    refresh_health()
    hurt_sound()
    damage_flash.alpha = 0.55
    damage_flash.animate('alpha', 0, duration=0.45)
    if player.health <= 0:
        player.health = 0
        game.player_died()


# GARDEN AND HOUSE - the walk-out ending - the peaceful ending

garden_root = Entity(enabled=False, position=GARDEN_OFFSET)


def tex_wall(texture_name, pos, scale, tint=color.white, rot=(0, 0, 0), tscale=(1, 1),
             col=True, keep=False):
    w = Entity(parent=garden_root, model='cube', texture=texture_name, color=tint,
               position=pos, scale=scale, rotation=rot,
               collider='box' if col else None)
    w.texture_scale = tscale
    w.garden_keep = keep
    return w


# keep=True on every line here: this is "the grass plain that is there" and
# to leave alone.
tex_wall('suburb_grass', (0, 0.02, 90), (140, 0.06, 140), tscale=(28, 28), col=True,
         keep=True)  # col=True or you fall through
FZ0, FZ1, FX = 20, 160, 70
tex_wall('darkwood', (0, 0.8, FZ1), (140, 1.6, 0.3), tint=RGB(60, 50, 40), tscale=(30, 1),
         keep=True)
tex_wall('darkwood', (-FX, 0.8, 90), (0.3, 1.6, 140), tint=RGB(60, 50, 40), tscale=(30, 1),
         keep=True)
tex_wall('darkwood', (FX, 0.8, 90), (0.3, 1.6, 140), tint=RGB(60, 50, 40), tscale=(30, 1),
         keep=True)
tex_wall('darkwood', (-37.5, 0.8, FZ0), (65, 1.6, 0.3), tint=RGB(60, 50, 40), tscale=(14, 1),
         keep=True)
tex_wall('darkwood', (37.5, 0.8, FZ0), (65, 1.6, 0.3), tint=RGB(60, 50, 40), tscale=(14, 1),
         keep=True)

# EVERY LINE FROM HERE TO GARDEN_SPAWN IS THE OLD HOUSE - the frist demo hosue i made a long time ago

BH = 6
tex_wall('darkwood', (0, 0.06, 100), (80, 0.1, 80), tscale=(16, 16))
tex_wall('suburb_brick_1', (0, BH / 2, 140), (80, BH, 0.5), tscale=(16, 3))
tex_wall('suburb_brick_1', (-40, BH / 2, 100), (0.5, BH, 80), tscale=(16, 3))
tex_wall('suburb_brick_1', (40, BH / 2, 100), (0.5, BH, 80), tscale=(16, 3))
tex_wall('suburb_brick_1', (-22.5, BH / 2, 60), (35, BH, 0.5), tscale=(8, 3))
tex_wall('suburb_brick_1', (22.5, BH / 2, 60), (35, BH, 0.5), tscale=(8, 3))
tex_wall('suburb_brick_1', (0, BH - 1, 60), (10, 2, 0.5), tscale=(3, 1))
tex_wall('whitedoor', (0, 2, 60), (4.5, 4, 0.4), tint=RGB(150, 110, 70))
tex_wall('ceiling', (0, BH + 0.1, 100), (82, 0.3, 82), tscale=(10, 10))
tex_wall('suburb_brick_2', (-25, BH + 2, 70), (20, 4, 12), tscale=(5, 2))
tex_wall('suburb_brick_2', (30, BH + 4, 130), (10, 8, 10), rot=(0, 12, 7), tscale=(3, 4))
tex_wall('ceiling', (30, BH + 8.4, 130), (12, 0.4, 12), rot=(0, 12, 7))
tex_wall('crungewallpaper', (0, BH / 2, 139.6), (79, BH, 0.2), tscale=(12, 3), col=False)
tex_wall('bluetilekitchen', (-28, 0.09, 128), (22, 0.08, 22), tscale=(8, 8), col=False)
tex_wall('oven', (-36, 1, 136), (3, 2, 2))
tex_wall('cupboard', (-30, 1, 136.5), (6, 2, 1.5))
tex_wall('cupboard', (-36, 3.4, 136.5), (8, 1.4, 1), col=False)
for gx, gt in ((-8, 'grandma'), (0, 'grandma2'), (8, 'grandma3')):
    tex_wall('darkwood', (gx, 3, 139.3), (3.4, 3.4, 0.1), col=False)
    tex_wall(gt, (gx, 3, 139.1), (3, 3, 0.05), col=False)
tex_wall('crungewallpaper', (-10, BH / 2, 100), (0.4, BH, 50), tscale=(8, 3))
tex_wall('crungewallpaper', (15, BH / 2, 100), (0.4, BH, 28), tscale=(5, 3))
tex_wall('funko', (38, 2, 138), (3.6, 3.6, 0.2), col=False)      # the easter egg

GARDEN_SPAWN = GARDEN_OFFSET + Vec3(0, 2, 35)

plot_exit_door = None


def build_plot():
    global plot_exit_door
    path = find_asset(ROOM_PLOT_GLB + '.glb', ROOM_PLOT_GLB + '.obj')
    if path is not None:
        print('%s: using your model, %s' % (ROOM_PLOT_NAME, path.name))
        # the hand-built garden steps aside rather than being deleted, so
        # taking your model back out again restores it
        for child in list(garden_root.children):
            child.enabled = False
        holder = Entity(parent=garden_root, scale=ROOM_PLOT_SCALE)
        model = Entity(parent=holder, model=ROOM_PLOT_GLB,
                       unlit=ROOM_PLOT_UNLIT, double_sided=True)
        if model.model is None:
            print('!! %s could not be loaded - the old garden is back'
                  % path.name)
            for child in list(garden_root.children):
                child.enabled = True
            destroy(holder)
        elif path.suffix.lower() == '.glb':
            try:
                tris = read_glb_triangles(path)
                xs = [v[0] for t in tris for v in t]
                ys = [v[1] for t in tris for v in t]
                zs = [v[2] for t in tris for v in t]
                floor, _fb = bake_floor_grid(tris, ROOM_PLOT_GRID,
                                             min(ys) + ROOM_PLOT_STAND_MAX)
                if floor:
                    Entity(parent=holder,
                           model=Mesh(vertices=floor, mode='triangle',
                                      static=True),
                           collider='mesh', visible=False)
                    print('   %s: floor baked to %d collision triangles from '
                          '%d, %.1f x %.1f x %.1fm'
                          % (ROOM_PLOT_NAME, len(floor) // 3, len(tris),
                             max(xs) - min(xs), max(ys) - min(ys),
                             max(zs) - min(zs)))
                if ROOM_PLOT_WALLS:
                    cx, cz = (min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2
                    w, d = max(xs) - min(xs), max(zs) - min(zs)
                    h = max(4.0, max(ys) - min(ys))
                    for px, pz, sx, sz in (
                            (min(xs), cz, 1.0, d + 2), (max(xs), cz, 1.0, d + 2),
                            (cx, min(zs), w + 2, 1.0), (cx, max(zs), w + 2, 1.0)):
                        Entity(parent=holder, model='cube', collider='box',
                               visible=False,
                               position=(px, min(ys) + h / 2, pz),
                               scale=(sx, h + 4, sz))
                    print('   %s: sealed, you cannot walk off the edge'
                          % ROOM_PLOT_NAME)
            except Exception as exc:
                print('!! %s collision failed (%s) - flat floor'
                      % (ROOM_PLOT_NAME, exc))
                Entity(parent=holder, model='cube', collider='box',
                       visible=False, position=(0, -0.5, 0),
                       scale=(200, 1, 200))

    # and the door home, model or no model
    tex = crunchy_texture(None, ROOM_PLOT_DOOR_TEX)
    if tex is None:
        print('!! %s.png not found - the door out of %s will be plain'
              % (ROOM_PLOT_DOOR_TEX, ROOM_PLOT_NAME))
    yaw = (ROOM_PLOT_DOOR_YAW if ROOM_PLOT_DOOR_YAW is not None
           else face_yaw(ROOM_PLOT_DOOR_AT, ROOM_PLOT_SPAWN))
    w, h = ROOM_PLOT_DOOR_SIZE
    plot_exit_door = Entity(
        parent=scene, model='quad',
        position=ROOM_PLOT_DOOR_AT + Vec3(0, h / 2, 0),
        rotation=(0, yaw, 0), scale=(w, h), texture=tex,
        color=color.white if tex else RGB(160, 130, 110),
        unlit=True, double_sided=True, collider='box', enabled=False)
    plot_exit_door.is_plot_exit = True
    print('%s: door back to the village at (%.1f, %.1f, %.1f) facing %.0f'
          % (ROOM_PLOT_NAME, ROOM_PLOT_DOOR_AT.x, ROOM_PLOT_DOOR_AT.y,
             ROOM_PLOT_DOOR_AT.z, yaw))


# Everything this uses is set up and explained in SECTION 1 next to
# FANTASY_HOUSE_GLB. This is only the doing of it.
FANTASY_HOUSE_ON = True

fantasy_house = None


def read_obj_triangles(path, flip_z=True, drop_below_z=None):
    verts, tris, dropped = [], [], 0
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            if line.startswith('v '):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith('f '):
                idx = []
                for part in line.split()[1:]:
                    n = int(part.split('/')[0])
                    idx.append(n - 1 if n > 0 else len(verts) + n)
                for k in range(1, len(idx) - 1):
                    try:
                        tri = (verts[idx[0]], verts[idx[k]], verts[idx[k + 1]])
                    except IndexError:
                        continue          # a face pointing at a vertex that
                        # does not exist. Skip it rather than fall over.
                    if (drop_below_z is not None
                            and max(v[2] for v in tri) < drop_below_z):
                        dropped += 1
                        continue
                    tris.append(tri)
    if dropped:
        print('   the marker cube: %d triangles dropped, they were past z=%.1f'
              % (dropped, drop_below_z))
    if flip_z:
        tris = [tuple((v[0], v[1], -v[2]) for v in t) for t in tris]
    return tris


def build_fantasy_house():
    global fantasy_house
    if not FANTASY_HOUSE_ON:
        print('THE PLOT: FANTASY_HOUSE_ON is False - the old garden stands')
        return

    glb = find_asset(FANTASY_HOUSE_GLB + '.glb')
    obj = find_asset(FANTASY_HOUSE_OBJ)
    if glb is None:
        print('!! %s.glb not found anywhere in the project - the old garden '
              'house stays. Drop the file in and it takes over.'
              % FANTASY_HOUSE_GLB)
        return

    hidden = 0
    for child in list(garden_root.children):
        if getattr(child, 'garden_keep', False):
            child.enabled = True
        else:
            child.enabled = False
            hidden += 1

    fantasy_house = Entity(parent=garden_root,
                           position=FANTASY_HOUSE_AT,
                           rotation=(0, FANTASY_HOUSE_YAW, 0),
                           scale=FANTASY_HOUSE_SCALE)
    model = Entity(parent=fantasy_house, model=FANTASY_HOUSE_GLB,
                   unlit=FANTASY_HOUSE_UNLIT, double_sided=True)
    if model.model is None:
        # it is on disk but panda3d could not read it, will fix later, hopefully wont forget.
        print('!! %s could not be loaded - the old garden is back' % glb.name)
        for child in list(garden_root.children):
            child.enabled = True
        destroy(fantasy_house)
        fantasy_house = None
        return
    # double_sided matters INSIDE: a wall modelled to be seen from the street
    # is a one-way pane of glass from the living room without it.

    if obj is None:
        print('!! %s not found - the house is a picture you can walk through. '
              'It needs to be somewhere in the project.' % FANTASY_HOUSE_OBJ)
    else:
        try:
            tris = read_obj_triangles(obj, flip_z=True,
                                      drop_below_z=FANTASY_HOUSE_CUBE_CUT)
            # DEGENERATE TRIANGLES - three points in a line, or two the same -
            # make panda3d print a warning per polygon and then collide with
            # nothing. There are always a few in an exported mesh, so they go
            # out here rather than filling up the log.
            verts = []
            thrown = 0
            for a, b, c in tris:
                ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
                wx, wy, wz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
                nx = uy * wz - uz * wy
                ny = uz * wx - ux * wz
                nz = ux * wy - uy * wx
                if nx * nx + ny * ny + nz * nz < 1e-14:
                    thrown += 1
                    continue
                verts += [a, b, c]
            Entity(parent=fantasy_house,
                   model=Mesh(vertices=verts, mode='triangle', static=True),
                   collider='mesh', visible=False)
            xs = [v[0] for v in verts]
            ys = [v[1] for v in verts]
            zs = [v[2] for v in verts]
            print('   the house is solid: %d collision triangles from your '
                  '.obj%s, %.1f x %.1f x %.1fm'
                  % (len(verts) // 3,
                     (' (%d degenerate ones thrown out)' % thrown) if thrown else '',
                     max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
        except Exception as exc:
            # LAST RESORT, and it is a worse house: one solid box the size of
            # the whole building. You cannot walk THROUGH it - but you cannot walk INTO it either, because
            # a box has no doorway. It is here so a broken .obj cannot leave
            # you falling through the ending, not because it is good.
            # The numbers are the model's own bounds in Ursina coordinates:
            # x -4.42..4.42, y 0..8.97, z -5.24..8.06, so centre z = 1.41.
            # just a failsafe
            print('!! the collision mesh failed (%s) - falling back to a solid '
                  'box the size of the house. You will not be able to get '
                  'inside it until this is fixed.' % exc)
            Entity(parent=fantasy_house, model='cube', collider='box',
                   visible=False, position=(0, 4.49, 1.41),
                   scale=(8.85, 8.97, 13.31))

    # 4 : the thanks picture, on the back wall inside
    art = crunchy_texture(None, FANTASY_HOUSE_ART, detail=FULL_DETAIL)
    if art is None:
        print('!! %s.png not found - the wall inside the house is bare'
              % FANTASY_HOUSE_ART)
    else:
        ax, ay = FANTASY_HOUSE_ART_AT
        aw = FANTASY_HOUSE_ART_WIDE
        # its real proportions, off the file, so the picture is not stretched
        ah = aw / ((art.width / art.height) if getattr(art, 'height', 0) else 1.0)
        # z here because the collider and the model are in Ursina's
        # coordinates and the wall was measured in the .obj's. Same flip,
        # same reason - see read_obj_triangles().
        Entity(parent=fantasy_house, model='cube',
               texture=FANTASY_HOUSE_ART_BOARD,
               color=RGB(60, 50, 40),
               position=(ax, ay, -(FANTASY_HOUSE_ART_Z + 0.05)),
               scale=(aw + 0.14, ah + 0.14, 0.05), unlit=True)
        Entity(parent=fantasy_house, model='cube', texture=art,
               position=(ax, ay, -FANTASY_HOUSE_ART_Z),
               scale=(aw, ah, 0.05), unlit=True)

    spawn = ROOM_PLOT_SPAWN
    print('THE PLOT: %s is up. %d pieces of the old house switched off, the '
          'grass and the fence kept.' % (glb.name, hidden))
    print('   it stands at garden-local (%.2f, %.2f, %.2f) turned %d degrees'
          % (FANTASY_HOUSE_AT.x, FANTASY_HOUSE_AT.y, FANTASY_HOUSE_AT.z,
             FANTASY_HOUSE_YAW))
    print('   you spawn on your cube, world (%.1f, %.1f, %.1f), facing the '
          'front door' % (spawn.x, spawn.y, spawn.z))
# NOTE: build_plot() is NOT called here. It needs face_yaw(),
# read_glb_triangles() and bake_floor_grid(), all of which are defined further
# down the file


# the SKY
#only ever switched on for the garden ending.
#
# THE HAPPY ENDING HAS ITS OWN SKY AND ITS OWN MUSIC
# bumpysky file  is the HAPPY ENDING sky and nothing else. Every
# other way of reaching the garden keeps the sky it always had.
#
# There is only ONE Sky object in this game and it is only ever switched on
# for the garden _go_garden() turns it on and clear_scenes() turns it off.
# So "only for the happy ending" was already almost true of the sky itself;
# what changes here is WHICH PICTURE it wears.

# The pacifist ending - the one where the scientist signs the house over to
# you, Game.ending_owned - swaps in bumpysky and swaps it back out on the way
# to the menu, so nothing else in the game can ever see it.
SKY_TEXTURE_DEFAULT = 'Enemy_MegafuckElite2'
SKY_TEXTURE_HAPPY   = 'bumpysky'

HAPPY_ENDING_MUSIC  = 'ifIevergetaroundtoliving'
HAPPY_ENDING_VOLUME = 0.34

sky = Sky(texture=SKY_TEXTURE_DEFAULT)
sky.enabled = False


def set_sky_texture(name):
    tex = crunchy_texture(None, name)
    if tex is None:
        print('!! sky texture %r not found - leaving the old one' % name)
        return False
    sky.texture = tex
    return True


# THE VILLAGE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! - ground, collision, street props

def read_glb_triangles(path, flip_z=True):
    import struct as _s
    with open(path, 'rb') as f:
        _s.unpack('<III', f.read(12))
        jl, _ = _s.unpack('<II', f.read(8))
        js = json.loads(f.read(jl).decode('utf-8'))
        _s.unpack('<II', f.read(8))
        blob = f.read()

    acc, views = js['accessors'], js['bufferViews']
    fmt = {5126: ('f', 4), 5123: ('H', 2), 5125: ('I', 4), 5121: ('B', 1)}

    def read(ai):
        a = acc[ai]
        v = views[a['bufferView']]
        base = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        parts = {'VEC4': 4, 'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a['type']]
        code, size = fmt[a['componentType']]
        stride = v.get('byteStride') or (size * parts)
        out_ = []
        for i in range(a['count']):
            chunk = _s.unpack_from('<' + code * parts, blob, base + i * stride)
            out_.append(chunk if parts > 1 else chunk[0])
        return out_
    # FOR EXPLANATION I USED AI CUZ THIS GOT CONCUSING

    # FULL 4x4 matrices, not just translation. A node can carry either an
    # explicit 'matrix' or a translation/rotation(quaternion)/scale triple,
    def mat_mul(a, b):
        return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)]
                for r in range(4)]

    def node_matrix(node):
        if 'matrix' in node:
            m = node['matrix']          # glTF stores it column-major
            return [[m[0], m[4], m[8], m[12]], [m[1], m[5], m[9], m[13]],
                    [m[2], m[6], m[10], m[14]], [m[3], m[7], m[11], m[15]]]
        tx, ty, tz = node.get('translation', [0, 0, 0])
        qx, qy, qz, qw = node.get('rotation', [0, 0, 0, 1])
        sx, sy, sz = node.get('scale', [1, 1, 1])
        # quaternion -> 3x3, then fold the scale into the columns
        r = [[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
             [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
             [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]]
        s = (sx, sy, sz)
        return [[r[0][0] * s[0], r[0][1] * s[1], r[0][2] * s[2], tx],
                [r[1][0] * s[0], r[1][1] * s[1], r[1][2] * s[2], ty],
                [r[2][0] * s[0], r[2][1] * s[1], r[2][2] * s[2], tz],
                [0, 0, 0, 1]]

    zk = -1.0 if flip_z else 1.0        # see the docstring - this is the fix

    def apply(m, v):
        return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2] + m[0][3],
                m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2] + m[1][3],
                (m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2] + m[2][3]) * zk)

    IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    out = []

    def walk(ni, parent_m):
        node = js['nodes'][ni]
        here = mat_mul(parent_m, node_matrix(node))
        if 'mesh' in node:
            for prim in js['meshes'][node['mesh']].get('primitives', []):
                if 'POSITION' not in prim.get('attributes', {}):
                    continue
                if prim.get('mode', 4) != 4:      # 4 = TRIANGLES; skip the rest
                    continue
                pos = read(prim['attributes']['POSITION'])
                idx = list(read(prim['indices'])) if 'indices' in prim \
                    else list(range(len(pos)))
                for k in range(0, len(idx) - 2, 3):
                    out.append(tuple(apply(here, pos[idx[k + m]]) for m in range(3)))
        for child in node.get('children', []):
            walk(child, here)

    for root in js['scenes'][js.get('scene', 0)]['nodes']:
        walk(root, IDENTITY)
    return out


def read_glb_by_material(path, flip_z=True):
    import struct as _s
    with open(path, 'rb') as f:
        _s.unpack('<III', f.read(12))
        jl, _ = _s.unpack('<II', f.read(8))
        js = json.loads(f.read(jl).decode('utf-8'))
        _s.unpack('<II', f.read(8))
        blob = f.read()

    acc, views = js['accessors'], js['bufferViews']
    fmt = {5126: ('f', 4), 5123: ('H', 2), 5125: ('I', 4), 5121: ('B', 1)}

    def read(ai):
        a = acc[ai]
        v = views[a['bufferView']]
        base = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        parts = {'VEC4': 4, 'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a['type']]
        code, size = fmt[a['componentType']]
        stride = v.get('byteStride') or (size * parts)
        out_ = []
        for i in range(a['count']):
            c = _s.unpack_from('<' + code * parts, blob, base + i * stride)
            out_.append(c if parts > 1 else c[0])
        return out_

    def mat_mul(a, b):
        return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)]
                for r in range(4)]

    def node_matrix(node):
        if 'matrix' in node:
            m = node['matrix']
            return [[m[0], m[4], m[8], m[12]], [m[1], m[5], m[9], m[13]],
                    [m[2], m[6], m[10], m[14]], [m[3], m[7], m[11], m[15]]]
        tx, ty, tz = node.get('translation', [0, 0, 0])
        qx, qy, qz, qw = node.get('rotation', [0, 0, 0, 1])
        sx, sy, sz = node.get('scale', [1, 1, 1])
        r = [[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
             [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
             [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]]
        s = (sx, sy, sz)
        return [[r[0][0] * s[0], r[0][1] * s[1], r[0][2] * s[2], tx],
                [r[1][0] * s[0], r[1][1] * s[1], r[1][2] * s[2], ty],
                [r[2][0] * s[0], r[2][1] * s[1], r[2][2] * s[2], tz],
                [0, 0, 0, 1]]

    zk = -1.0 if flip_z else 1.0        # see read_glb_triangles

    def apply(m, v):
        return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2] + m[0][3],
                m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2] + m[1][3],
                (m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2] + m[2][3]) * zk)

    names = {i: m.get('name', 'mat%d' % i)
             for i, m in enumerate(js.get('materials', []))}
    groups = {}
    IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

    def walk(ni, parent_m):
        node = js['nodes'][ni]
        here = mat_mul(parent_m, node_matrix(node))
        if 'mesh' in node:
            for prim in js['meshes'][node['mesh']].get('primitives', []):
                attrs = prim.get('attributes', {})
                if 'POSITION' not in attrs or prim.get('mode', 4) != 4:
                    continue
                pos = read(attrs['POSITION'])
                uv = read(attrs['TEXCOORD_0']) if 'TEXCOORD_0' in attrs else None
                idx = list(read(prim['indices'])) if 'indices' in prim \
                    else list(range(len(pos)))
                name = names.get(prim.get('material'), 'unnamed')
                vl, ul = groups.setdefault(name, ([], []))
                for k in range(0, len(idx) - 2, 3):
                    for m in range(3):
                        j = idx[k + m]
                        vl.append(apply(here, pos[j]))
                        # glTF UVs run top-down, Ursina's run bottom-up
                        ul.append((uv[j][0], 1.0 - uv[j][1]) if uv else (0, 0))
        for child in node.get('children', []):
            walk(child, here)

    for root in js['scenes'][js.get('scene', 0)]['nodes']:
        walk(root, IDENTITY)
    return groups


# city_root itself gets created near the top of SECTION 10 now - the red door
# needs it before this point. Everything below still attaches to it as before.
#
# THE SOVIET VILLAGE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# The cemetery is gone, that was my original village. New is a real village: 37,376 triangles, 128 x 81 metres
# It arrived as DachaFAB.blend and nothing else, so it gets read straight out
# of the .blend the same way the office desk was. ONE THING TO KNOW , everything is rotated wrongly in the original file
# so its a huge headache.

VILLAGE_OBJ    = 'village.obj'
VILLAGE_NAV    = 'village_nav.json'
VILLAGE_SCALE  = 1.0

VILLAGE_TEXTURES = {
    'phong1':   'Dedinaru5b',    # walls, windows, doors
    'phong2':   'Dedinaru5c',    # roofs and trim
    'None.001': 'GrassBrown',    # the ground plane
    'None':     'GrassBrown',
}
# How many times each texture repeats across a surface. See the note above
# (1, 1) is normal, bigger numbers smear and look deliberately wrong.
VILLAGE_TEXTURE_SCALE = {
    'phong1':   (1, 1),
    'phong2':   (1, 1),
    'None.001': (1, 1),
    'None':     (1, 1),
}

village = None
village_bounds = None
village_parts = []


def chunk_triangles_xz(vlist, ulist, size):
    if not size or size <= 0:
        return [(vlist, ulist)]
    cells = {}
    for t in range(0, len(vlist) - 2, 3):
        cx = (vlist[t][0] + vlist[t + 1][0] + vlist[t + 2][0]) / 3.0
        cz = (vlist[t][2] + vlist[t + 1][2] + vlist[t + 2][2]) / 3.0
        key = (int(math.floor(cx / size)), int(math.floor(cz / size)))
        bucket = cells.setdefault(key, ([], []))
        bucket[0].extend((vlist[t], vlist[t + 1], vlist[t + 2]))
        bucket[1].extend((ulist[t], ulist[t + 1], ulist[t + 2]))
    return [v for v in cells.values() if v[0]]


def build_village():
    global village_bounds
    obj = find_asset(VILLAGE_OBJ)
    if obj is None:
        print(f'!! {VILLAGE_OBJ} not found - the village folder needs to be in the project')
        return None
    holder = Entity(parent=city_root, scale=VILLAGE_SCALE)
    groups = load_obj_by_material(obj, flip_x=False, shade=False)
    tris = 0
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for name, (vlist, ulist, _c) in groups.items():
        if not vlist:
            continue
        tris += len(vlist) // 3
        for v in vlist:
            for i in range(3):
                lo[i] = min(lo[i], v[i])
                hi[i] = max(hi[i], v[i])
        mat = name.split('__')[-1]
        tex_name = VILLAGE_TEXTURES.get(mat)
        if tex_name is None:
            print(f'   village: no texture mapped for material {mat!r}')
        # FPS: the half-size copies (Dedinaru5b_low.png etc, generated once)
        # are tried first - a quarter of the pixels for a look you cannot
        # tell apart through the fog. Falls back to the full-size original.
        tex = None
        if tex_name:
            tex = crunchy_texture(obj.parent, tex_name + '_low')
            if tex is None:
                tex = crunchy_texture(obj.parent, tex_name)
                print(f'   village: no {tex_name}_low.png, using full-size '
                      f'{tex_name} (slower)')
        # CUT INTO CHUNKS SO CULLING CAN WORK!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # MAKING A FOG AND CHUNKS MIGHT HAV EBEEN THE MOST CONFUSING THING IN THIS WHOLE GAME

        #Before this code !!!, each material was ONE mesh spanning the whole village,
        # so its bounding box was the whole map: always intersecting the
        # camera frustum, never rejectable, all 37,376 triangles submitted
        # every frame however thick the fog was or wherever i stood.
        #
        # Cut into VILLAGE_CHUNK-metre columns, each piece gets a small
        # bounding box and Panda3D's own culling throws away everything behind
        # you and everything past CLIP_FAR - which, with fog ending at 26m, is
        # most of the village most of the time.
        #
        # Chunked by the triangle's CENTRE, so a triangle is never split and
        # nothing can end up with a hole in it.
        for cell_verts, cell_uvs in chunk_triangles_xz(vlist, ulist,
                                                       VILLAGE_CHUNK):
            part = Entity(parent=holder,
                          model=Mesh(vertices=cell_verts, uvs=cell_uvs,
                                     mode='triangle', static=True),
                          texture=tex,
                          color=color.white if tex else RGB(150, 145, 135),
                          double_sided=True, unlit=True)
            # the tiling dial. See the big note on VILLAGE_TEXTURES.
            ts = VILLAGE_TEXTURE_SCALE.get(mat)
            if ts and ts != (1, 1):
                part.texture_scale = ts
            part.group_name = name
            village_parts.append(part)
    village_bounds = (lo[0], hi[0], lo[2], hi[2])
    print('village: %d triangles in %d chunks (%s), %.0f x %.0fm, %.1fm tall'
          % (tris, len(village_parts),
             ('%.0fm cells' % VILLAGE_CHUNK) if VILLAGE_CHUNK > 0 else 'chunking off',
             hi[0] - lo[0], hi[2] - lo[2], hi[1] - lo[1]))
    return holder


village = build_village()


# Both come out of village_nav.json, baked from the mesh itself rather than
# placed by hand. The bake rasterised all 37k triangles into a half-metre grid
VILLAGE_WALL_MIN = 2.0
VILLAGE_GROUND_LIFT = 0.04  # you stand a hair above the mesh, never inside it

# THE FLOOR COLLIDER WAS THE BIGGEST SINGLE COST IN THE VILLAGE FOR FPS
# It used to be built at every 2nd cell of a 515 x 325 grid, which is 83,268
# collision triangles. Panda3D keeps a CollisionPolygon per triangle and tests
# rays against the lot, and it is all resident in memory for the whole game -
# by a wide margin the most expensive thing in the scene.

# At 4 it's 20,838 triangles - a quarter of the geometry, visually and
# physically identical to walk on. Drop it to 2 if i ever add real terrain
# with sharp steps; push it to 6 or 8 for more speed on a slower machine.

VILLAGE_FLOOR_STEP = 8
# ONE FLAT COLLIDER FOR THE WHOLE VILLAGE
# See the long note inside build_village_collision(). True = one box, no
# elevation anywhere, nothing can sink into the ground. False = the old shaped
# floor that follows the terrain.
VILLAGE_FLOOR_FLAT  = True
VILLAGE_FLAT_Y      = 0.0    # the one height the whole village stands at
VILLAGE_FLAT_THICK  = 4.0    # how deep the slab is, so you cannot fall past it

village_ground = None       # lookup function
village_walls = []
village_wall_boxes = []     # world-space (cx, cz, sx, sz, y_lo, y_hi) per box
village_floor = None
# THE EDGE OF THE VILLAGE, TAKEN FROM THE COLLISION FILE
# village_bounds gets worked out from village.obj when the MODEL loads. This
# is the same thing worked out from village_nav.json when the COLLISION loads,
# and it exists because the two can fail independently.
#
# I found this by actually running the game with the assets missing: if the
# .obj is not there but the .json is, you get a village you can walk around
# in with no bounds recorded - and the villagers then had nowhere to put a
# navmesh and quietly did not appear at all.
village_nav_bounds = None   # (x0, x1, z0, z1) or None


def build_village_collision():
    global village_floor, village_nav_bounds
    path = find_asset(VILLAGE_NAV)
    if path is None:
        print(f'!! {VILLAGE_NAV} not found - no collision, you will fall through')
        return lambda x, z: 0.0
    with open(path) as f:
        nav = json.load(f)
    cell = nav['cell'] * VILLAGE_SCALE
    x0, z0 = nav['x0'] * VILLAGE_SCALE, nav['z0'] * VILLAGE_SCALE
    nx, nz = nav['nx'], nav['nz']
    g = nav['ground']
    village_nav_bounds = (x0, x0 + nx * cell, z0, z0 + nz * cell)

    def height_at(x, z):
        fx = clamp((x - x0) / cell, 0, nx - 1.001)
        fz = clamp((z - z0) / cell, 0, nz - 1.001)
        ix, iz = int(fx), int(fz)
        tx, tz = fx - ix, fz - iz
        h00, h10 = g[ix][iz], g[ix + 1][iz]
        h01, h11 = g[ix][iz + 1], g[ix + 1][iz + 1]
        return (lerp(lerp(h00, h10, tx), lerp(h01, h11, tx), tz)
                * VILLAGE_SCALE + VILLAGE_GROUND_LIFT)


    # WHY THIS FIXES THE SINKING - I KEPT HAVING PROBLEMS WITH DIFFERENT HEIGHTS OF THE FLOOW
    # WHICH ALL OF THIS IS MOSTLY ABOUT

    if VILLAGE_FLOOR_FLAT:
        flat_y = VILLAGE_FLAT_Y
        wide = (nx * cell) + 40
        deep = (nz * cell) + 40
        floor = Entity(parent=city_root, model='cube', collider='box',
                       visible=False,
                       position=(x0 + nx * cell / 2,
                                 flat_y - VILLAGE_FLAT_THICK / 2,
                                 z0 + nz * cell / 2),
                       scale=(wide, VILLAGE_FLAT_THICK, deep))
        village_floor = floor
        # every wall box still comes from the code  below, so the buildings
        # are exactly where they were
        for gx, gz, w, h, lo, hi in nav.get('rects', []):
            cx = x0 + (gx + w / 2) * cell
            cz = z0 + (gz + h / 2) * cell
            tall = max(0.6, (hi - lo) * VILLAGE_SCALE)
            village_walls.append(Entity(
                parent=city_root, model='cube', collider='box', visible=False,
                position=(cx, lo * VILLAGE_SCALE + tall / 2, cz),
                scale=(w * cell, tall, h * cell)))
            village_wall_boxes.append((cx, cz, w * cell, h * cell,
                                       lo * VILLAGE_SCALE,
                                       lo * VILLAGE_SCALE + tall))

        return lambda x, z: flat_y

    # The floor you actually walk on !!!!!!
    # See the VILLAGE_FLOOR_STEP note above
    # this one number is the biggest performance dial in the village.
    step = VILLAGE_FLOOR_STEP
    verts, uvs = [], []
    for i in range(0, nx - step, step):
        for k in range(0, nz - step, step):
            ax, az = x0 + i * cell, z0 + k * cell
            bx, bz = x0 + (i + step) * cell, z0 + (k + step) * cell
            L = VILLAGE_GROUND_LIFT
            p00 = (ax, g[i][k] + L, az)
            p10 = (bx, g[i + step][k] + L, az)
            p01 = (ax, g[i][k + step] + L, bz)
            p11 = (bx, g[i + step][k + step] + L, bz)
            verts += [p00, p11, p10, p00, p01, p11]
            uvs += [(0, 0), (1, 1), (1, 0), (0, 0), (0, 1), (1, 1)]
    floor = Entity(parent=city_root,
                   model=Mesh(vertices=verts, uvs=uvs, mode='triangle', static=True),
                   collider='mesh', visible=False)

    # the walls
    for gx, gz, w, h, lo, hi in nav.get('rects', []):
        cx = x0 + (gx + w / 2) * cell
        cz = z0 + (gz + h / 2) * cell
        tall = max(0.6, (hi - lo) * VILLAGE_SCALE)
        village_walls.append(Entity(
            parent=city_root, model='cube', collider='box', visible=False,
            position=(cx, lo * VILLAGE_SCALE + tall / 2, cz),
            scale=(w * cell, tall, h * cell)))
        # kept in world units for the house-picker below: centre, footprint,
        # bottom and top of every wall box
        village_wall_boxes.append((cx, cz, w * cell, h * cell,
                                   lo * VILLAGE_SCALE,
                                   lo * VILLAGE_SCALE + tall))
    patched = close_village_wall_gaps(nav, x0, z0, cell)
    print('village collision: %d floor triangles, %d wall boxes (%d gap patches)'
          % (len(verts) // 3, len(village_walls), patched))
    village_floor = floor
    return height_at


# THE RULE: ONLY FILL A HOLE THAT HAS WALL ON BOTH SIDES

VILLAGE_GAP_FILL = True
VILLAGE_GAP_MAX  = 1.00     # metres. The widest hole treated as a window.


def close_village_wall_gaps(nav, x0, z0, cell):
    if not VILLAGE_GAP_FILL:
        return 0
    try:
        nx, nz = nav['nx'], nav['nz']
        max_gap = max(1, int(VILLAGE_GAP_MAX / cell))

        grid = [bytearray(nz) for _ in range(nx)]
        for gx, gz, w, h, lo, hi in nav.get('rects', []):
            for i in range(gx, min(nx, gx + w)):
                row = grid[i]
                for k in range(gz, min(nz, gz + h)):
                    row[k] = 1

        # the patches, as (i, k) also remember a height to build them at
        patch = set()

        def scan_line(cells, put):
            n = len(cells)
            i = 0
            while i < n:
                if cells[i]:
                    i += 1
                    continue
                start = i
                while i < n and not cells[i]:
                    i += 1
                # wall on BOTH sides, and short enough to be a hole
                if start > 0 and i < n and (i - start) <= max_gap:
                    for j in range(start, i):
                        put(j)

        for i in range(nx):
            scan_line(grid[i], lambda k, i=i: patch.add((i, k)))
        for k in range(nz):
            column = bytearray(grid[i][k] for i in range(nx))
            scan_line(column, lambda i, k=k: patch.add((i, k)))

        if not patch:
            return 0
# AT THIS POINT IM COMPLETELY LOST!

        # a sensible height: as tall as the walls around here. Taking the
        # tallest rect in the whole village would build 5m posts in gaps
        # between garden sheds, so it uses the median instead.
        heights = sorted((hi - lo) for _, _, _, _, lo, hi in nav.get('rects', []))
        tall = max(1.2, heights[len(heights) // 2] * VILLAGE_SCALE) if heights else 2.5
        base = min((lo for _, _, _, _, lo, hi in nav.get('rects', [])), default=0.0)

        # merge runs along x so it is a few dozen boxes, not six hundred
        made = 0
        by_row = {}
        for i, k in patch:
            by_row.setdefault(k, []).append(i)
        for k, xs in by_row.items():
            xs.sort()
            run_start = prev = xs[0]
            for i in xs[1:] + [None]:
                if i is not None and i == prev + 1:
                    prev = i
                    continue
                w = prev - run_start + 1
                cx = x0 + (run_start + w / 2.0) * cell
                cz = z0 + (k + 0.5) * cell
                village_walls.append(Entity(
                    parent=city_root, model='cube', collider='box',
                    visible=False,
                    position=(cx, base * VILLAGE_SCALE + tall / 2, cz),
                    scale=(w * cell, tall, cell)))
                village_wall_boxes.append((cx, cz, w * cell, cell,
                                           base * VILLAGE_SCALE,
                                           base * VILLAGE_SCALE + tall))
                made += 1
                if i is not None:
                    run_start = prev = i
        return made
    except Exception as exc:
        print('!! could not patch the wall gaps: %s' % exc)
        return 0


village_ground = build_village_collision()
terrain_height = village_ground          # the rest of the game calls it this
cemetery_floor = village_floor           # kept so older references still resolve
cemetery_bounds = village_bounds
cemetery_colliders = village_walls


def set_clip(scene_name):
    camera.clip_plane_far = CLIP_FAR.get(scene_name, 1000)


def set_scene_fog(on, col=None, density=None):
    global _fog_node
    if not on:
        # `scene` sits under panda3d's `render`, and fog is INHERITED down the
        # graph - so clearing it on the scene is not enough if anything ever put it on the node above. Both get cleared, and the camera too.
        # Collected defensively rather than named directly, because `render` is a panda3d builtin rather than an ursina export and I would rather this
        # function degrade than raise in the middle of a scene change.
        targets = [scene]
        try:
            targets.append(application.base.render)
        except Exception:
            pass
        targets.append(camera)
        for node in targets:
            try:
                node.clearFog()
            except Exception:
                pass
        try:
            scene.fog_density = 0        # keep Ursina's own property
        except Exception:
            pass
        _fog_node = None
        return

    try:
        from panda3d.core import Fog as _PandaFog
        fog = _PandaFog('scene_fog')
        fog.setColor(col[0], col[1], col[2])
        fog.setLinearRange(density[0], density[1])
        scene.setFog(fog)
        _fog_node = fog
    except Exception as exc:
        # if panda3d ever moves that class, fall back to Ursina's own setters
        print('!! direct fog failed (%s), using ursina properties' % exc)
        scene.fog_color = col
        scene.fog_density = density


_fog_node = None


def mix_color(a, b, t):
    t = clamp(t, 0.0, 1.0)
    return Vec4(lerp(a[0], b[0], t), lerp(a[1], b[1], t),
                lerp(a[2], b[2], t), 1.0)


def fog_is_on():
    try:
        return scene.getFog() is not None
    except Exception:
        return _fog_node is not None


class WallColliderLOD(Entity):
    def __init__(self):
        super().__init__()
        self.t = 0.0
        self.next_wall = 0

    def update(self):
        if game is None or not city_root.enabled or game.state not in ('office', 'ending'):
            return
        self.t -= time.dt
        if self.t > 0:
            return
        self.t = WALL_COLLIDER_TICK
        r2 = WALL_COLLIDER_RADIUS * WALL_COLLIDER_RADIUS
        px, pz = player.x, player.z


        # This loop used to do all 996 walls in one frame. That is fine
        count = len(village_walls)
        changed = 0
        looked = 0
        i = self.next_wall
        while looked < count:
            wall = village_walls[i]
            box = village_wall_boxes[i]
            on = (box[0] - px) ** 2 + (box[1] - pz) ** 2 < r2
            if wall.enabled != on:
                wall.enabled = on
                changed += 1
                if changed >= WALL_SWITCH_BUDGET:
                    # stop here and pick up from the next one in a moment
                    self.next_wall = (i + 1) % count
                    return
            i = (i + 1) % count
            looked += 1
        self.next_wall = i


wall_collider_lod = WallColliderLOD()


# THE FIVE NPC HOUSES - doors and interiors ALL MY TEXTURES!!!


house_root = Entity(enabled=False)      # all five interiors live under this
village_houses = []                     # dicts: door, outside spawn, room idx
house_npcs = []                         # every NPC, for the look-at-player loop
house_rooms = []                        # dicts: spawn, face, exit door entity
_houses_built = False


def cluster_wall_boxes(gap=HOUSE_CLUSTER_GAP):
    n = len(village_wall_boxes)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]      # path compression
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    CELL = 4.0
    grid = {}
    for i, b in enumerate(village_wall_boxes):
        grid.setdefault((int(b[0] // CELL), int(b[1] // CELL)), []).append(i)

    for i, b in enumerate(village_wall_boxes):
        gx, gz = int(b[0] // CELL), int(b[1] // CELL)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for j in grid.get((gx + dx, gz + dz), ()):
                    if j <= i:
                        continue
                    c = village_wall_boxes[j]
                    if (abs(b[0] - c[0]) <= (b[2] + c[2]) / 2 + gap
                            and abs(b[1] - c[1]) <= (b[3] + c[3]) / 2 + gap):
                        union(i, j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    out = []
    for members in groups.values():
        xs0 = min(village_wall_boxes[i][0] - village_wall_boxes[i][2] / 2 for i in members)
        xs1 = max(village_wall_boxes[i][0] + village_wall_boxes[i][2] / 2 for i in members)
        zs0 = min(village_wall_boxes[i][1] - village_wall_boxes[i][3] / 2 for i in members)
        zs1 = max(village_wall_boxes[i][1] + village_wall_boxes[i][3] / 2 for i in members)
        ylo = min(village_wall_boxes[i][4] for i in members)
        yhi = max(village_wall_boxes[i][5] for i in members)
        out.append(((xs0 + xs1) / 2, (zs0 + zs1) / 2,
                    xs1 - xs0, zs1 - zs0, ylo, yhi))
    return out


def pick_house_boxes():
    if not village_wall_boxes:
        print('!! no village collision boxes - no houses can be placed. '
              'Check village_nav.json loaded.')
        return []
    clusters = cluster_wall_boxes()
    cands = [c for c in clusters
             if HOUSE_MIN_SIZE <= c[2] <= HOUSE_MAX_SIZE
             and HOUSE_MIN_SIZE <= c[3] <= HOUSE_MAX_SIZE
             and (c[5] - c[4]) >= HOUSE_MIN_HEIGHT
             and math.hypot(c[0] - OFFICE_ORIGIN_XZ.x,
                            c[1] - OFFICE_ORIGIN_XZ.y) > 8.0]
    cands.sort(key=lambda c: math.hypot(c[0] - OFFICE_ORIGIN_XZ.x,
                                        c[1] - OFFICE_ORIGIN_XZ.y))
    print(f'houses: {len(village_wall_boxes)} wall slabs welded into '
          f'{len(clusters)} buildings, {len(cands)} of them house-sized')
    picked = cands[:HOUSE_COUNT]
    if len(picked) < HOUSE_COUNT:
        print(f'!! only {len(picked)} houses found near the office - that many '
              f'get doors instead of {HOUSE_COUNT}. Loosen HOUSE_MIN_SIZE / '
              f'HOUSE_MAX_SIZE if you want more.')
    for c in picked:
        print('   house at (%.1f, %.1f)  %.1f x %.1f m  %.1fm from the office'
              % (c[0], c[1], c[2], c[3],
                 math.hypot(c[0] - OFFICE_ORIGIN_XZ.x, c[1] - OFFICE_ORIGIN_XZ.y)))
    return picked


# _skin_panel() and _roof_pyramid() used to live here - the two helpers that
# built the wall patches and the extra roof cap. Both features are gone, so
# the helpers went with them rather than sitting here never being called.


def load_house_data():
    path = find_asset(HOUSE_DATA_FILE)
    if path is None:
        print(f'!! {HOUSE_DATA_FILE} not found - falling back to guessing houses '
              f'from the collision bake, which is known to be inaccurate. '
              f'Run tools_rebuild_houses.py to regenerate it.')
        return []
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        print(f'!! could not read {HOUSE_DATA_FILE}: {e}')
        return []
    data.sort(key=lambda h: math.hypot(h['cx'] - OFFICE_ORIGIN_XZ.x,
                                       h['cz'] - OFFICE_ORIGIN_XZ.y))
    return data


HOUSE_FILL_SOLID = False   # do not turn this back on. See above.


def seal_village_houses():
    return 0


def door_outward(yaw):
    r = math.radians(yaw)
    return Vec3(-math.sin(r), 0, -math.cos(r))


def build_village_doors():
    if not HOUSE_DOOR_POSITIONS:
        print('   (HOUSE_DOOR_POSITIONS is empty - falling back to finding the '
              'houses from the model, which is the old inaccurate way)')
        return build_house_reskins()

    for i, pos in enumerate(HOUSE_DOOR_POSITIONS[:HOUSE_COUNT]):
        door_tex = HOUSE_DOOR_TEXTURES[i % len(HOUSE_DOOR_TEXTURES)]

        # WHICH WAY IT FACES. Your five doors sit either side of the road that
        # runs along x at about z = 0, so "face the road" means face -z from
        # the far side and +z from the near side. One line, and overridable.
        yaw = None
        if i < len(HOUSE_DOOR_YAW):
            yaw = HOUSE_DOOR_YAW[i]
        if yaw is None:
            yaw = 0.0 if pos.z >= 0 else 180.0
        out_dir = door_outward(yaw)

        # WHERE I LAND WHEN I COME BACK OUT. Two and a half metres out in
        # front of the door - far enough that arriving there is not inside the
        # door's own collider, which is what used to bounce the player in and out.
        step_out = HOUSE_WALK_IN_RANGE + 1.1
        probe = pos + out_dir * step_out

        # THE GROUND OUTSIDE. Your y is floor level where you were standing,
        # so it is already right for the door. The nav bake only gets
        # consulted for the step-out spot, and only believed if it agrees with
        # your y to within a metre and a half - because that bake records the
        # tops of buildings as ground in places, which is what put an earlier
        # set of doors three metres up in the air.
        ground_out = pos.y
        if village_ground:
            navy = village_ground(probe.x, probe.z)
            if abs(navy - pos.y) < 1.5:
                ground_out = navy
            else:
                print('   (door %d: nav ground %.2f disagrees with your y %.2f '
                      'at the step-out spot - using yours)' % (i + 1, navy, pos.y))

        tex = crunchy_texture(None, door_tex)
        if tex is None:
            print('!! house door texture missing: %s.png - door %d will be a '
                  'plain brown slab until it is in the project'
                  % (door_tex, i + 1))
        door = Entity(parent=city_root, model='quad',
                      position=Vec3(pos.x, pos.y + HOUSE_DOOR_SIZE[1] / 2, pos.z),
                      rotation=(0, yaw, 0), scale=HOUSE_DOOR_SIZE,
                      texture=tex,
                      color=color.white if tex else RGB(150, 120, 110),
                      unlit=True, double_sided=True, collider='box')
        door.is_house_door = True
        door.house_index = i

        label = Text(str(i + 1), parent=city_root, billboard=True, origin=(0, 0),
                     position=Vec3(pos.x,
                                   pos.y + HOUSE_DOOR_SIZE[1] + HOUSE_NUMBER_LIFT,
                                   pos.z),
                     scale=HOUSE_NUMBER_SCALE, color=RGB(255, 240, 90))
        label.setFogOff(1)         # stays readable through the village fog

        village_houses.append(dict(door=door,
                                   outside=Vec3(probe.x, ground_out + 0.25, probe.z),
                                   room=(HOUSE_DOOR_ROOM[i]
                                         if i < len(HOUSE_DOOR_ROOM) else i),
                                   label=label))
        locked = HOUSE_LOCKED_UNTIL.get(i)
        print('   door %d at (%7.2f, %5.2f, %6.2f)  floor y=%.2f  facing %3.0f'
              '  %s%s'
              % (i + 1, pos.x, pos.y, pos.z, pos.y, yaw, door_tex,
                 '  [locked until door %d]' % (locked + 1) if locked is not None
                 else ''))
    print('doors: %d placed from your coordinates, %.1f x %.1fm each'
          % (len(village_houses), HOUSE_DOOR_SIZE[0], HOUSE_DOOR_SIZE[1]))


def build_house_reskins():
    houses = load_house_data()
    if not houses:
        houses = [dict(cx=c[0], cz=c[1], sx=c[2], sz=c[3],
                       base=c[4], eaves=c[4] + (c[5] - c[4]) * 0.62, apex=c[5])
                  for c in pick_house_boxes()]

    for i, h in enumerate(houses[:HOUSE_COUNT]):
        cx, cz, sx, sz = h['cx'], h['cz'], h['sx'], h['sz']
        base, eaves, apex = h['base'], h['eaves'], h['apex']
        wall_tex = HOUSE_WALL_TEXTURES[i % len(HOUSE_WALL_TEXTURES)]
        trim_tex = HOUSE_TRIM_TEXTURES[i % len(HOUSE_TRIM_TEXTURES)]
        door_tex = HOUSE_DOOR_TEXTURES[i % len(HOUSE_DOOR_TEXTURES)]

        # I used to paste small random texture patches onto the house walls
        # here to break them up on blender , plus an extra roof cap and an extra collider
        # box. All three are gone: the patches looked like damage rather than
        # decoration, the real roof is already a roof, and the village's own
        # baked collision makes the houses solid without help.

        # THE DOOR
        # It replaces the painted-on door of the village house rather than
        # adding a building: same wall, same street side, just a way in.
        #This is basically the door mechanism for how they appear infront of the asset village doors
        to_office = Vec2(OFFICE_ORIGIN_XZ.x - cx, OFFICE_ORIGIN_XZ.y - cz)
        if abs(to_office.x) > abs(to_office.y):
            side = 1 if to_office.x > 0 else -1
            dx, dz, yaw = cx + side * (sx / 2 + HOUSE_SKIN_INSET + 0.05), cz, 90
        else:
            side = 1 if to_office.y > 0 else -1
            dx, dz, yaw = cx, cz + side * (sz / 2 + HOUSE_SKIN_INSET + 0.05), 0

        # The facing and the direction the player steps out to are recomputed from where
        # you put it, so a door on a different wall still works the exact same way with the same code
        override = HOUSE_DOOR_OVERRIDE.get(i)
        if override is not None:
            dx, dz = override.x, override.y
            if abs(dx - cx) / max(sx, 0.01) > abs(dz - cz) / max(sz, 0.01):
                yaw, side = 90, (1 if dx > cx else -1)
            else:
                yaw, side = 0, (1 if dz > cz else -1)
            print('   house %d: using your door coordinates (%.2f, %.2f)'
                  % (i + 1, dx, dz))

        # THE DOOR'S HEIGHT: from the MODEL - I RAN OUT OF TIME AND THIS DOOR SECTION IS MADE WITH AI - ITS WAY TOO COMPLICATED FOR NO REASON
        # Sampled a couple of metres OUTSIDE the wall, on the open ground you
        # will actually be standing on when you walk up to the door. Sampling
        # at the door itself asks the bake how high the HOUSE is, not how high
        # the ground is, which is what returned 2.85 under house 1.
        step_out = HOUSE_WALK_IN_RANGE + 1.0
        probe = Vec3(dx, 0, dz)
        if yaw == 90:
            probe.x += side * step_out
        else:
            probe.z += side * step_out

        ground = base
        if village_ground:
            navy = village_ground(probe.x, probe.z)
            if abs(navy - base) < 1.5:      # sane: open ground near the house
                ground = navy
            else:
                print('   (house %d: nav ground %.2f is nowhere near the '
                      'foundation %.2f - using the foundation)'
                      % (i + 1, navy, base))
        tex = crunchy_texture(None, door_tex)
        if tex is None:
            print(f'!! house door texture missing: {door_tex}')
        door = Entity(parent=city_root, model='quad',
                      position=Vec3(dx, ground + HOUSE_DOOR_SIZE[1] / 2, dz),
                      rotation=(0, yaw, 0), scale=HOUSE_DOOR_SIZE,
                      texture=tex, color=color.white if tex else RGB(150, 120, 110),
                      unlit=True, double_sided=True, collider='box')
        door.is_house_door = True
        door.house_index = i

        #theres a NUMBER floating over the door for clarity because this got very annoying

        label = Text(str(i + 1), parent=city_root, billboard=True, origin=(0, 0),
                     position=Vec3(dx, ground + HOUSE_DOOR_SIZE[1] + HOUSE_NUMBER_LIFT, dz),
                     scale=HOUSE_NUMBER_SCALE, color=RGB(255, 240, 90))
        label.setFogOff(1)         # stays readable through the village fog

        # where you reappear when you leave: the same open spot we just probed
        out = Vec3(probe.x, ground + 0.25, probe.z)
        village_houses.append(dict(door=door, outside=out, room=i, label=label))
        print('   house %d at (%6.2f,%6.2f) %4.1fx%4.1f  walls->%.2f roof->%.2f  '
              '%s / %s  door on %s face'
              % (i + 1, cx, cz, sx, sz, eaves, apex, wall_tex, trim_tex,
                 ('+x' if side > 0 else '-x') if yaw == 90
                 else ('+z' if side > 0 else '-z')))
    print(f'houses: {len(village_houses)} numbered doors placed')


build_village_doors()


def fit_npc_model(holder, model_name, target=NPC_TARGET_HEIGHT):
    # veritytm.glb is a rigged character with eight animations in it, and
    # loading it threw before it ever reached the mesh:
    use_name = model_name
    if find_asset(model_name + '_static.glb'):
        use_name = model_name + '_static'

    try:
        ent = Entity(parent=holder, model=use_name, unlit=False)
    except Exception as e:
        print('!! %s could not be loaded by Ursina (%s: %s)'
              % (use_name, type(e).__name__, e))
        if use_name == model_name:
            print('   -> run:  python tools_static_glb.py %s.glb   and it '
                  'will almost certainly load' % model_name)
        return None
    if ent.model is None:
        destroy(ent)
        return None
    if use_name != model_name:
        print('   (using %s - the original has animation data Ursina cannot '
              'read)' % use_name)
    ent.rotation_y = NPC_MODEL_YAW.get(model_name, NPC_MODEL_YAW['default'])

    ent.rotation_x = NPC_MODEL_PITCH.get(model_name, 0)

    try:

        b = ent.getTightBounds(holder)
        height = (b[1][1] - b[0][1]) or 1.0
        k = target / height
        ent.scale = k

        b2 = ent.getTightBounds(holder)
        ent.y -= b2[0][1]
        span = (b[1][0] - b[0][0], height, b[1][2] - b[0][2])
        print('npc %s: %.2f x %.2f x %.2f units -> %.2fm tall, scale %.4f%s'
              % (model_name, span[0], span[1], span[2], target, k,
                 ' (stood upright)' if ent.rotation_x else ''))
    except Exception as e:
        print(f'!! could not measure {model_name}, standing it as-is:', e)
    return ent


def build_placeholder_npc(holder):
    tex = crunchy_texture(None, random.choice(HOUSE_DOOR_TEXTURES))
    Entity(parent=holder, model='cube', position=(0, 0.62, 0),
           scale=(0.52, 1.24, 0.30), color=RGB(70, 62, 70), unlit=True,
           texture=crunchy_texture(None, 'crungewallpaper'))
    head = Entity(parent=holder, model='cube', position=(0, 1.48, 0),
                  scale=(0.34, 0.40, 0.34), texture=tex,
                  color=color.white if tex else RGB(200, 180, 170), unlit=True)
    return head


def npc_script(room):
    if room is None or room not in NPC_LINES:
        # not silent and not identical - anybody without a script of
        # their own says a few things out of the village pool
        return ('SOMEBODY', random_village_lines(seed=9000 + (room or 0)))
    return NPC_LINES[room]


def build_npc(holder_pos, kind, face_toward, room=None):
    pivot = Entity(parent=house_root, position=holder_pos)
    if kind == 'scientist':
        if fit_npc_model(pivot, NPC_SCIENTIST_GLB) is None:
            print(f'!! {NPC_SCIENTIST_GLB}.glb failed to load - placeholder NPC')
            build_placeholder_npc(pivot)
    elif kind == 'dj':
        # veritytm.glb - skinned, so Ursina's loader gets first go because it
        # is the only one that understands the skeleton. fit_npc_model()
        # measures whatever comes back and scales it to NPC_TARGET_HEIGHT, so
        # he cannot arrive the wrong size either way.
        if fit_npc_model(pivot, NPC_DJ_GLB, NPC_DJ_HEIGHT) is None:
            print('!! %s.glb failed to load - placeholder DJ' % NPC_DJ_GLB)
            build_placeholder_npc(pivot)
        else:
            # HIS FEET. fit_npc_model has already put them on the pivot's
            # origin; this lifts him clear of a floor that is not quite
            # where the coordinate said. See NPC_DJ_LIFT.
            pivot.y = pivot.y + NPC_DJ_LIFT
            print('   THE DJ: feet at y=%.2f (floor was read as %.2f, lifted '
                  'by %.2f). Stand there and press T - if the numbers differ, '
                  'put the difference in NPC_DJ_LIFT.'
                  % (pivot.y, NPC_DJ_AT.y, NPC_DJ_LIFT))
    elif kind == 'gmanjake':
        # his own builder, because he is an .obj with six materials and
        # no textures of his own - see build_jake_model.
        if build_jake_model(pivot, random.Random(31)) is None:
            build_placeholder_npc(pivot)
    elif kind == 'handsatwaist':
        # THE BLENDER 5 PROBLEM THIS IS SUCH A NICHE RANDOM THING BUT handsatwaist.blend is saved in Blender 5.02's
        # format (its header literally reads BLENDER17-01v0502) and that format
        # can only be opened by Blender 5 itself - no Python library reads it,
        # and Ursina cannot load a .blend at all unless Blender is installed
        # and on the PATH to convert it.

        # So the game looks for an EXPORT instead, under any of the obvious
        # names, and stands a placeholder there until it finds one. The moment
        # i drop handsatwaist.glb anywhere in the project it gets picked up
        # with no code change at all.

        #THIS COULD BE FIXED WITH A CORRECT EXPORT BUT I RAN OUT OF TIME AND DIDNT DEAL WITH IT, SO I USED AI TO MAKE IT WORK!!!
        got = None
        for stem in ('handsatwaist', 'handsatwaist_export', 'hands_at_waist',
                     'handsatwaist1'):
            if find_asset(f'{stem}.glb', f'{stem}.obj', f'{stem}.gltf'):
                got = fit_npc_model(pivot, stem)
                if got is not None:
                    print(f'   shop NPC: using {stem}')
                    break
        if got is None:
            print('!! handsatwaist: no export found, placeholder standing in. '
                  'In Blender: File > Export > glTF 2.0, save it as '
                  'handsatwaist.glb anywhere in the project.')
            build_placeholder_npc(pivot)
    else:
        build_placeholder_npc(pivot)
    d = face_toward - holder_pos
    pivot.rotation_y = math.degrees(math.atan2(d.x, d.z))
    pivot.is_npc = True
    pivot.talk_name, pivot.talk_lines = npc_script(room)
    #RECORDING, if this room has one. See ROOM_VOICES: Jake loops,
    # the scientist and the DJ play once. A room with no row here uses the
    # shared NPC voice and loops, exactly as before for any dialogue
    _row = ROOM_VOICES.get(room)
    pivot.talk_voice = _row['voice'] if _row else None
    pivot.talk_voice_loops = _row['loop'] if _row else True
    pivot.npc_room = room          # so the scientist can be recognised
    pivot.talked = False
    # a box you can point at. Roughly a person: as wide as your shoulders and
    # as tall as NPC_TARGET_HEIGHT, which is what every model here is scaled
    # to, so one size genuinely fits all of them.
    pivot.collider = BoxCollider(pivot,
                                 center=Vec3(0, NPC_TARGET_HEIGHT / 2, 0),
                                 size=Vec3(0.75, NPC_TARGET_HEIGHT, 0.75))
    house_npcs.append(pivot)
    return pivot

# EVERY INTERIOR EXIT DOOR, DECIDED IN ONE PLACE

# The rule is: the door you leave a house by is the SAME DOOR you came in
# through. Not a similar door - the same picture, so the shop's door has the
# shop's picture on the inside of it and the DJ's has his.
#
# It gets read off HOUSE_DOOR_ROOM rather than typed out, which matters
# because that list is not in order (door 1 opens room 1, door 2 opens room 0) becasue i wrote it stupidly

def face_yaw(pos, target):
    d = Vec3(target) - Vec3(pos)
    if abs(d.x) < 1e-6 and abs(d.z) < 1e-6:
        return 0.0
    return math.degrees(math.atan2(-d.x, -d.z))


def clip_to_box(vlist, ulist, half_x, half_z, max_y):
    out_v, out_u, dropped = [], [], 0
    for t in range(0, len(vlist) - 2, 3):
        tri = (vlist[t], vlist[t + 1], vlist[t + 2])
        if all(abs(v[0]) <= half_x and abs(v[2]) <= half_z and v[1] <= max_y
               for v in tri):
            out_v.extend(tri)
            out_u.extend((ulist[t], ulist[t + 1], ulist[t + 2]))
        else:
            dropped += 1
    return out_v, out_u, dropped


def room_exit_door_texture(room):
    if room is None:
        return ROOM_EXIT_DOOR_FALLBACK_TEX
    for door, opens in enumerate(HOUSE_DOOR_ROOM):
        if opens == room and door < len(HOUSE_DOOR_TEXTURES):
            return HOUSE_DOOR_TEXTURES[door]
    return ROOM_EXIT_DOOR_FALLBACK_TEX


def room_exit_door_size(room):
    return (ROOM_EXIT_DOOR_WIDTH,
            ROOM_EXIT_DOOR_HEIGHT.get(room, ROOM_EXIT_DOOR_HEIGHT_DEFAULT))


def room_exit_door(room, floor_pos, yaw):
    size = room_exit_door_size(room)
    tex = room_exit_door_texture(room)
    print('   room %s: exit door %.2f x %.2fm, %r, facing %.0f deg'
          % (room, size[0], size[1], tex, yaw))
    return make_exit_door(Vec3(floor_pos) + Vec3(0, size[1] / 2, 0),
                          yaw, tex, size)


def make_exit_door(pos, yaw, tex_name=None, size=None):
    if tex_name is None:
        tex_name = ROOM_EXIT_DOOR_FALLBACK_TEX
    if size is None:
        size = (ROOM_EXIT_DOOR_WIDTH, ROOM_EXIT_DOOR_HEIGHT_DEFAULT)
    tex = crunchy_texture(None, tex_name)
    if tex is None:
        print(f'!! exit door texture missing: {tex_name}')

    d = Entity(parent=house_root, model='quad', position=pos,
               rotation=(0, yaw, 0), scale=size, texture=tex,
               color=color.white if tex else RGB(200, 195, 185),
               unlit=True, double_sided=True,
               # no collider, so an interior door can never be the thing
               # standing between you and the room it belongs to
               collider='box' if ROOM_EXIT_DOORS_SOLID else None)
    d.is_room_exit = True
    return d


def build_room_corridor(base):
    holder = Entity(parent=house_root, position=base)
    room = Entity(parent=holder, model=ROOM_CORRIDOR_GLB, unlit=False)
    if room.model is None:
        print(f'!! {ROOM_CORRIDOR_GLB}.glb did not load - room 1 is a void, '
              'check the file is next to launcher.py')
    # collision straight off the glb's triangles, like the DOOM map does it
    glb_path = find_asset(f'{ROOM_CORRIDOR_GLB}.glb')
    if glb_path:
        try:
            tris = read_glb_triangles(glb_path)
            verts = [v for tri in tris for v in tri]
            ys = [v[1] for v in verts]
            print(f'room corridor: {len(tris)} collision triangles, '
                  f'y {min(ys):.1f}..{max(ys):.1f} (expect about -4..6)')
            Entity(parent=holder,
                   model=Mesh(vertices=verts, mode='triangle', static=True),
                   collider='mesh', visible=False)
        except Exception as e:
            print('!! corridor collision failed, floor boxes instead:', e)
            Entity(parent=holder, model='cube', collider='box', visible=False,
                   position=(-3.8, 3.7, 8.2), scale=(3, 0.4, 5))

    exit_door = room_exit_door(0, base + ROOM_CORRIDOR_EXIT,
                               ROOM_CORRIDOR_EXIT_YAW)
    npc = build_npc(base + ROOM_CORRIDOR_NPC, 'scientist',
                    base + ROOM_CORRIDOR_SPAWN, room=0)
    return dict(spawn=base + ROOM_CORRIDOR_SPAWN, face=ROOM_CORRIDOR_FACE,
                exit=exit_door, npc=npc)


def build_room_shop(base):
    S = ROOM_SHOP_SCALE
    holder = Entity(parent=house_root, position=base, scale=S)

    def M(p):
        return base + Vec3(p.x * S, p.y * S, p.z * S)

    path = find_asset(f'{ROOM_SHOP_GLB}.glb')
    if path is None:
        print(f'!! {ROOM_SHOP_GLB}.glb not found - the shop will be an empty '
              f'room. Put it anywhere in the project.')
        Entity(parent=holder, model='cube', collider='box', visible=False,
               position=(0, ROOM_SHOP_FLOOR - 0.5, 0), scale=(20, 1, 14))
    else:
        # one entity per material, each with its own wrong texture
        try:
            groups = read_glb_by_material(path)
        except Exception as e:
            print('!! could not split the shop by material (%s) - loading it '
                  'whole instead, so the crazy textures will not apply' % e)
            groups = {}
            Entity(parent=holder, model=ROOM_SHOP_GLB, unlit=False)

        spare = 0
        kept_tris = dropped_tris = 0
        for name, (vlist, ulist) in groups.items():
            if not vlist:
                continue
            # DROP THE OUTSIDE OFF THE HOUSE
            if name in ROOM_SHOP_DROP_MATERIALS:
                dropped_tris += len(vlist) // 3
                continue
            vlist, ulist, _cut = clip_to_box(
                vlist, ulist, ROOM_SHOP_KEEP_X, ROOM_SHOP_KEEP_Z,
                ROOM_SHOP_KEEP_Y)
            dropped_tris += _cut
            kept_tris += len(vlist) // 3
            if not vlist:
                continue
            skin = SHOP_MATERIAL_SKINS.get(name)
            if skin is None:
                skin = (SHOP_SPARE_SKINS[spare % len(SHOP_SPARE_SKINS)], (6, 6))
                spare += 1
                print(f'   shop: material {name!r} not in SHOP_MATERIAL_SKINS, '
                      f'using {skin[0]}')
            tex_name, tscale = skin
            tex = crunchy_texture(None, tex_name, ROOM_SHOP_TEXTURE_DETAIL)
            if tex is None:
                print(f'!! shop texture missing: {tex_name} (material {name})')
            piece = Entity(parent=holder,
                           model=Mesh(vertices=vlist, uvs=ulist,
                                      mode='triangle', static=True),
                           texture=tex,
                           color=color.white if tex else RGB(150, 140, 150),
                           double_sided=True, unlit=True)
            # STRETCHED ON PURPOSE. Unequal, non-tiling numbers so the image
            # smears differently on every surface - THIS BARELY WORKED
            piece.texture_scale = tscale

        # real collision, off the asset's own triangles - but only the ones
        # left inside the building, for the same reason the visuals are cut
        try:
            tris = read_glb_triangles(path)

            tris = [t for t in tris
                    if abs((t[0][0] + t[1][0] + t[2][0]) / 3) <= ROOM_SHOP_KEEP_X
                    and abs((t[0][2] + t[1][2] + t[2][2]) / 3) <= ROOM_SHOP_KEEP_Z
                    and min(v[1] for v in t) <= ROOM_SHOP_KEEP_Y]
            Entity(parent=holder,
                   model=Mesh(vertices=[v for t in tris for v in t],
                              mode='triangle', static=True),
                   collider='mesh', visible=False)
            print('   shop: %d materials skinned at detail x%.2f, %d visible '
                  'triangles kept / %d thrown away as "outside", %d collision '
                  'triangles, scaled %.2f (ceiling %.2fm)'
                  % (len(groups), ROOM_SHOP_TEXTURE_DETAIL, kept_tris,
                     dropped_tris, len(tris), S, (7.0 - ROOM_SHOP_FLOOR) * S))
        except Exception as e:
            print('!! shop collision failed (%s) - flat floor instead' % e)
            Entity(parent=holder, model='cube', collider='box', visible=False,
                   position=(0, ROOM_SHOP_FLOOR - 0.5, 0), scale=(20, 1, 14))

    # THE DOOR, in the doorway
    Entity(parent=house_root, model='cube', collider='box', visible=False,
           position=Vec3(base.x, ROOM_SHOP_SPAWN_WORLD.y - ROOM_SHOP_FLOOR_DROP
                         - 0.5, base.z),
           scale=(ROOM_SHOP_KEEP_X * 2 * S, 1.0, ROOM_SHOP_KEEP_Z * 2 * S))
    print('   shop: safety floor at y=%.2f across %.1f x %.1fm'
          % (ROOM_SHOP_SPAWN_WORLD.y - ROOM_SHOP_FLOOR_DROP,
             ROOM_SHOP_KEEP_X * 2 * S, ROOM_SHOP_KEEP_Z * 2 * S))


    _yaw = (ROOM_SHOP_EXIT_YAW if ROOM_SHOP_EXIT_YAW is not None
            else face_yaw(ROOM_SHOP_EXIT_WORLD, ROOM_SHOP_SPAWN_WORLD))
    exit_door = room_exit_door(1, ROOM_SHOP_EXIT_WORLD, _yaw)
    npc = build_npc(M(ROOM_SHOP_NPC), 'handsatwaist', ROOM_SHOP_SPAWN_WORLD,
                    room=1)
    return dict(spawn=Vec3(ROOM_SHOP_SPAWN_WORLD),
                face=ROOM_SHOP_FACE, exit=exit_door, npc=npc)


def build_jake_model(pivot, rng):
    obj = find_asset(NPC_JAKE_OBJ + '.obj')
    if obj is None:
        print('!! %s.obj not found - Jake falls back to the placeholder'
              % NPC_JAKE_OBJ)
        return None
    holder = Entity(parent=pivot)
    groups = load_obj_by_material(obj, flip_x=False, shade=True)
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for mat, (vlist, ulist, clist) in groups.items():
        if not vlist:
            continue
        for v in vlist:
            for i in range(3):
                lo[i] = min(lo[i], v[i])
                hi[i] = max(hi[i], v[i])
        want = NPC_JAKE_TEXTURES.get(mat)
        tex = crunchy_texture(None, want) if want else None
        if want and tex is None:
            print('!! Jake: %s.png missing for material %s' % (want, mat))
        Entity(parent=holder,
               model=Mesh(vertices=vlist, uvs=ulist, colors=clist,
                          mode='triangle', static=True),
               texture=tex,
               color=color.white if tex else RGB(150, 145, 150),
               double_sided=True, unlit=True)
    raw_h = max(0.001, hi[1] - lo[1])
    k = NPC_JAKE_HEIGHT / raw_h
    holder.scale = k
    holder.y = -lo[1] * k          # feet on the floor, whatever the origin might be
    holder.rotation_y = NPC_JAKE_YAW
    print('   Jake: %.1f units tall -> scale %.4f, standing %.2fm'
          % (raw_h, k, raw_h * k))
    return holder


def build_room_jake(base):
    holder = Entity(parent=house_root, position=base, scale=ROOM_JAKE_SCALE)
    room = Entity(parent=holder, model=ROOM_JAKE_GLB, unlit=False,
                  double_sided=True)
    if room.model is None:
        print('!! %s.glb did not load - Jake gets a plain box instead'
              % ROOM_JAKE_GLB)
        Entity(parent=holder, model='cube', collider='box', visible=False,
               position=(0, -0.5 / ROOM_JAKE_SCALE, 0),
               scale=(300, 1, 400))
    else:
        path = find_asset(ROOM_JAKE_GLB + '.glb')
        try:
            tris = read_glb_triangles(path)
            Entity(parent=holder,
                   model=Mesh(vertices=[v for t in tris for v in t],
                              mode='triangle', static=True),
                   collider='mesh', visible=False)
            print('   Jake room: %d collision triangles, scaled %.4f '
                  '(ceiling %.2fm)' % (len(tris), ROOM_JAKE_SCALE,
                                       96.0 * ROOM_JAKE_SCALE))
        except Exception as exc:
            print('!! Jake room collision failed (%s) - flat floor' % exc)
            Entity(parent=holder, model='cube', collider='box', visible=False,
                   position=(0, -15, 0), scale=(300, 30, 400))

    # the toilet, in the corner, at chair height - peak
    toilet = Entity(parent=house_root,
                    position=ROOM_JAKE_TOILET_WORLD,       # yours
                    rotation_y=ROOM_JAKE_TOILET_YAW,
                    model=ROOM_JAKE_TOILET_GLB,
                    scale=ROOM_JAKE_TOILET_SCALE, unlit=False)
    if toilet.model is None:
        print('!! %s.glb did not load - no toilet in the corner'
              % ROOM_JAKE_TOILET_GLB)
        destroy(toilet)
    else:
        print('   Jake room: toilet at %.2fm tall in the corner'
              % (8.51 * ROOM_JAKE_TOILET_SCALE))

    # THE DOOR IN THE WEIRDO LEVEL
    exit_door = room_exit_door(2, ROOM_JAKE_EXIT_WORLD, ROOM_JAKE_EXIT_YAW)
    npc = build_npc(ROOM_JAKE_NPC_WORLD, 'gmanjake',
                    ROOM_JAKE_SPAWN_WORLD, room=2)
    return dict(spawn=Vec3(ROOM_JAKE_SPAWN_WORLD), face=ROOM_JAKE_FACE,
                exit=exit_door, npc=npc)


def read_glb_material_colours(path):
    out = {}
    try:
        with open(path, 'rb') as f:
            struct = __import__('struct')
            struct.unpack('<III', f.read(12))
            jl, _ = struct.unpack('<II', f.read(8))
            js = json.loads(f.read(jl).decode('utf-8'))
        for m in js.get('materials', []):
            c = m.get('pbrMetallicRoughness', {}).get('baseColorFactor',
                                                      [1, 1, 1, 1])
            out[m.get('name', '')] = tuple(c)
    except Exception as exc:
        print('!! could not read the material colours from %s (%s)'
              % (getattr(path, 'name', path), exc))
    return out


def build_dj_bedframe(base):
    if not DJ_BEDFRAME_ON:
        return
    path = find_asset(DJ_BEDFRAME_OBJ + '.obj')
    if path is None:
        print('!! %s.obj not found - no bed frame under the decks'
              % DJ_BEDFRAME_OBJ)
        return
    try:
        groups = load_obj_by_material(path, flip_x=False, shade=True)
    except Exception as exc:
        print('!! could not read %s.obj (%s)' % (DJ_BEDFRAME_OBJ, exc))
        return
    if not groups:
        return

    xs = [v[0] for _m, (vl, _u, _c) in groups.items() for v in vl]
    ys = [v[1] for _m, (vl, _u, _c) in groups.items() for v in vl]
    zs = [v[2] for _m, (vl, _u, _c) in groups.items() for v in vl]
    if not xs:
        return
    long_axis = max(max(xs) - min(xs), max(zs) - min(zs)) or 1.0
    k = DJ_BEDFRAME_LONG / long_axis
    low = min(ys)
    holder = Entity(parent=house_root,
                    position=base + DJ_BEDFRAME_AT + Vec3(0, DJ_BEDFRAME_LIFT, 0),
                    rotation=(0, DJ_BEDFRAME_YAW, 0))
    for _mat, (vl, ul, cl) in groups.items():
        if not vl:
            continue
        moved = [((v[0]) * k, (v[1] - low) * k, (v[2]) * k) for v in vl]
        Entity(parent=holder,
               model=Mesh(vertices=moved, uvs=ul, colors=cl,
                          mode='triangle', static=True),
               color=RGB(150, 140, 130), double_sided=True, unlit=True)

    # antoher blunder and usign ai here because I just don tunderstand whats wrong????
    Entity(parent=holder, model='cube', collider='box', visible=False,
           position=(0, 0.22, 0), scale=(DJ_BEDFRAME_LONG, 0.45, 1.0))
    at = holder.world_position
    print('   dj bedframe: at world (%.2f, %.2f, %.2f), %.2fm long, '
          'under the decks' % (at.x, at.y, at.z, DJ_BEDFRAME_LONG))


def build_room_dj(base):
    holder = Entity(parent=house_root, position=base, scale=ROOM_DJ_SCALE)
    holder.y = base.y - ROOM_DJ_GRASS_Y * ROOM_DJ_SCALE

    # the void it floats in!
    Entity(parent=house_root, model='sphere', position=base, scale=400,
           double_sided=True, unlit=True, color=ROOM_DJ_VOID_COLOUR)

    path = find_asset(ROOM_DJ_GLB + '.glb')
    groups, spare, tris_n = {}, 0, 0
    if path is None:
        print('!! %s.glb not found - the DJ gets a flat green floor'
              % ROOM_DJ_GLB)
    else:
        try:
            groups = read_glb_by_material(path)
        except Exception as exc:
            print('!! could not split %s by material (%s) - loading it whole, '
                  'so the white surfaces will still be white' % (ROOM_DJ_GLB, exc))
            Entity(parent=holder, model=ROOM_DJ_GLB, unlit=False,
                   double_sided=True)
    for name, (vlist, ulist) in groups.items():
        if not vlist:
            continue
        tris_n += len(vlist) // 3
        skin = ROOM_DJ_SKINS.get(name)
        if skin is None:
            skin = (ROOM_DJ_SPARE_SKINS[spare % len(ROOM_DJ_SPARE_SKINS)], (3, 3))
            spare += 1
            print('   DJ house: material %r is not in ROOM_DJ_SKINS, using %s'
                  % (name, skin[0]))
        tex_name, tscale = skin
        tex = crunchy_texture(None, tex_name, ROOM_DJ_TEXTURE_DETAIL)
        if tex is None:
            print('!! DJ house: %s.png missing for material %s - that surface '
                  'will be plain, not white' % (tex_name, name))
        piece = Entity(parent=holder,
                       model=Mesh(vertices=vlist, uvs=ulist, mode='triangle',
                                  static=True),
                       texture=tex,
                       color=color.white if tex else RGB(120, 130, 110),
                       double_sided=True, unlit=True)
        piece.texture_scale = tscale
    if groups:
        print('   DJ house: %d materials, all skinned, %d triangles - nothing '
              'left untextured' % (len(groups), tris_n))

    # THE FLOOR, AND THE WALLS
    #the garden is flat, and a flat thing needs a flat collider.
    Entity(parent=house_root, model='cube', collider='box', visible=False,
           position=Vec3(base.x, ROOM_DJ_FLOOR_Y - 0.5, base.z),
           scale=(ROOM_DJ_HALF * 2 + 4, 1.0, ROOM_DJ_HALF * 2 + 4))
    for dx, dz, sx, sz in ((-1, 0, 1.0, ROOM_DJ_HALF * 2),
                           (1, 0, 1.0, ROOM_DJ_HALF * 2),
                           (0, -1, ROOM_DJ_HALF * 2, 1.0),
                           (0, 1, ROOM_DJ_HALF * 2, 1.0)):
        Entity(parent=house_root, model='cube', collider='box', visible=False,
               position=Vec3(base.x + dx * ROOM_DJ_HALF,
                             ROOM_DJ_FLOOR_Y + ROOM_DJ_WALL_H / 2,
                             base.z + dz * ROOM_DJ_HALF),
               scale=(sx, ROOM_DJ_WALL_H, sz))
    print('   DJ house: flat floor at y=%.2f, %.0f x %.0fm, walled in'
          % (ROOM_DJ_FLOOR_Y, ROOM_DJ_HALF * 2, ROOM_DJ_HALF * 2))

    if ROOM_DJ_SOLID_WALLS and groups:
        by_size = sorted(((len(vl) // 3, m, vl) for m, (vl, _u) in groups.items()
                          if m != ROOM_DJ_GRASS and vl), reverse=True)
        walls, used = [], 0
        for n_tris, m, vl in by_size:
            if used + n_tris <= ROOM_DJ_WALL_BUDGET or not walls:
                walls += vl
                used += n_tris
        if walls:
            Entity(parent=holder,
                   model=Mesh(vertices=walls, mode='triangle', static=True),
                   collider='mesh', visible=False)
            print('   DJ house: buildings solid, %d collision triangles '
                  '(budget %d)' % (len(walls) // 3, ROOM_DJ_WALL_BUDGET))

    # THE DECKS
    deck_path = find_asset(ROOM_DJ_SET_GLB + '.glb')
    deck_at = ROOM_DJ_SET_WORLD + Vec3(0, ROOM_DJ_SET_LIFT, 0)
    deck_yaw = face_yaw(ROOM_DJ_SET_WORLD, ROOM_DJ_NPC_WORLD) + 180
    decks = Entity(parent=house_root, position=deck_at, rotation_y=deck_yaw,
                   scale=ROOM_DJ_SET_SCALE)
    made = 0
    if deck_path is not None:
        colours = read_glb_material_colours(deck_path)
        tex = crunchy_texture(None, ROOM_DJ_SET_TEXTURE)
        try:
            for name, (vlist, ulist) in read_glb_by_material(deck_path).items():
                if not vlist:
                    continue
                c = colours.get(name, (0.7, 0.7, 0.7, 1.0))
                # its own colour, brightened a little so the black parts read
                tint = RGB(min(255, 40 + c[0] * 215), min(255, 40 + c[1] * 215),
                           min(255, 40 + c[2] * 215))
                Entity(parent=decks,
                       model=Mesh(vertices=vlist, uvs=ulist, mode='triangle',
                                  static=True),
                       texture=tex, color=tint, unlit=True, double_sided=True)
                made += 1
        except Exception as exc:
            print('!! could not build the decks by material (%s)' % exc)
    if made:

        # I wanted the dj set to have a collider so you cannot walk through it.
        # A box round the console rather than a mesh collider: it is a
        # rectangular table, a box is exact enough, and it costs one collision
        # solid instead of a few hundred.
        try:
            db = decks.getTightBounds()
            dw = max(0.2, db[1][0] - db[0][0])
            dh = max(0.2, db[1][1] - db[0][1])
            dd = max(0.2, db[1][2] - db[0][2])
            Entity(parent=decks, model='cube', collider='box', visible=False,
                   position=(0, dh / 2, 0), scale=(dw, dh, dd))
        except Exception as exc:
            print('!! could not measure the decks for a collider (%s)' % exc)
        print('   DJ house: decks %d parts, %.2fm wide, at (%.1f, %.1f, %.1f) '
              'turned %.0f to face the DJ'
              % (made, 17.39 * ROOM_DJ_SET_SCALE, deck_at.x, deck_at.y,
                 deck_at.z, deck_yaw))
    else:
        print('!! %s.glb could not be built - no decks' % ROOM_DJ_SET_GLB)
        destroy(decks)

    # the way out, at your coordinate, facing where you land
    door = room_exit_door(3, ROOM_DJ_EXIT_WORLD,
                          face_yaw(ROOM_DJ_EXIT_WORLD, ROOM_DJ_SPAWN_WORLD))

    npc = build_npc(ROOM_DJ_NPC_WORLD, 'dj', ROOM_DJ_SPAWN_WORLD, room=3)
    build_dj_bedframe(base)
    return dict(spawn=Vec3(ROOM_DJ_SPAWN_WORLD),
                face=face_yaw(ROOM_DJ_SPAWN_WORLD, ROOM_DJ_NPC_WORLD) + 180,
                exit=door, npc=npc)


def build_room_placeholder(base, n):
    holder = Entity(parent=house_root, position=base)
    wall_tex = crunchy_texture(None, 'crungewallpaper')
    floor_tex = crunchy_texture(None, 'darkwood')
    ceil_tex = crunchy_texture(None, 'ceiling')
    W, H = 8.0, 3.0
    Entity(parent=holder, model='cube', position=(0, -0.05, 0),
           scale=(W, 0.1, W), texture=floor_tex, unlit=True, collider='box',
           texture_scale=(4, 4))
    Entity(parent=holder, model='cube', position=(0, H + 0.05, 0),
           scale=(W, 0.1, W), texture=ceil_tex, unlit=True, texture_scale=(4, 4))
    for px, pz, sx, sz in ((0, -W / 2, W, 0.2), (0, W / 2, W, 0.2),
                           (-W / 2, 0, 0.2, W), (W / 2, 0, 0.2, W)):
        Entity(parent=holder, model='cube', position=(px, H / 2, pz),
               scale=(sx, H, sz), texture=wall_tex, unlit=True,
               collider='box', texture_scale=(4, 2))
    exit_door = room_exit_door(n, base + Vec3(0, 0, W / 2 - 0.15), 0)
    # spawn kept well clear of the door, or arriving re-triggers it instantly, very annoying
    npc = build_npc(base + Vec3(0, 0, -W / 2 + 1.6), 'placeholder',
                    base + Vec3(0, 0, W / 2 - 2.2), room=n)
    return dict(spawn=base + Vec3(0, 0.2, W / 2 - 2.2), face=180,
                exit=exit_door, npc=npc)


ROOM_BUILDERS = [build_room_corridor, build_room_shop,
                 build_room_jake,                       # grandma3
                 build_room_dj,                         # grandma - the DJ
                 lambda b: build_room_placeholder(b, 4)]


def ensure_houses_built():
    global _houses_built
    if _houses_built:
        return
    _houses_built = True
    started = time.time()
    for n, builder in enumerate(ROOM_BUILDERS):
        base = ROOM_BASE + Vec3(n * ROOM_SPACING, 0, 0)
        try:
            house_rooms.append(builder(base))
        except Exception as e:
            print(f'!! room {n} failed to build ({e}) - plain box instead')
            house_rooms.append(build_room_placeholder(base, n))
    print(f'interiors: {len(house_rooms)} rooms built in '
          f'{time.time() - started:.1f}s')

class NPCWatcher(Entity):
    def update(self):
        if game is None or game.state != 'house' or not house_root.enabled:
            return
        here = player.world_position
        for npc in house_npcs:
            #Mixing local and world coordinates
            # is the exact bug that broke the red door for me for weeks - see the
            # note in Game.update - so it does not get repeated here.
            at = npc.world_position
            want = math.degrees(math.atan2(here.x - at.x, here.z - at.z))
            npc.rotation_y = lerp_angle(npc.rotation_y, want, min(1, time.dt * 4))


npc_watcher = NPCWatcher()


class TerrainClamp(Entity):
    def update(self):
        if village_ground is None or not city_root.enabled:
            return
        if game is None or game.state not in ('office', 'ending'):
            return
        if GODMODE:
            return
        floor = village_ground(player.x, player.z)
        if player.y < floor:
            player.y = floor
            player.grounded = True


terrain_clamp = TerrainClamp()


def ground_under(x, z, fallback=0.0):
    hit = raycast(Vec3(x, 60, z), Vec3(0, -1, 0), distance=200, ignore=(player,))
    if hit.hit:
        return hit.world_point.y
    return village_ground(x, z) if village_ground else fallback


# B makes every collider visible. STILL IN THE GAME I THINK IT SSUPER USEFUL. If something is solid where it shouldn't be,
# or you can walk through a wall, turn this on if yo uare lost or something is broken like it always is, see exactly what is the problem pretty much.
COLLIDER_VIEW = False
_collider_ghosts = []


def toggle_collider_view():
    global COLLIDER_VIEW
    COLLIDER_VIEW = not COLLIDER_VIEW
    for ghost in _collider_ghosts:
        try:
            destroy(ghost)
        except Exception:
            pass
    _collider_ghosts.clear()
    if not COLLIDER_VIEW:
        test_note('colliders hidden')
        return
    count = 0
    for e in scene.entities:
        if getattr(e, 'collider', None) is None or not e.enabled or e is player:
            continue
        if e is village_floor:
            tint = RGB(90, 255, 120, 60)
        elif e in village_walls:
            tint = RGB(255, 70, 70, 110)
        else:
            tint = RGB(110, 170, 255, 110)
        try:
            ghost = Entity(model='cube', position=e.world_position,
                           rotation=e.world_rotation, scale=e.world_scale,
                           color=tint, unlit=True, double_sided=True)
            _collider_ghosts.append(ghost)
            count += 1
        except Exception:
            continue
    test_note(f'{count} colliders  -  green ground, red walls, blue props')


SNOW_TEXTURED = False # i took this out a while ago cuzthe particles slow down the game A TONNNNNNNNNNNNN
# a lot of my features were too big and the game wasnt able to run them i think its lowk because of the enginewhich isnt that powerful OR ITS JUST MY HORRIBLY
#OPTIMISED CODE

SNOW_COUNT   = 0         # was 34. Snow is off for FPS.
SNOW_BOX     = 18.0      # metres across the volume around you  (was 26)
SNOW_TOP     = 11.0      # how far above your head they start
SNOW_FALL    = (1.6, 3.4)      # metres per second, randomised per flake
SNOW_DRIFT   = 0.5       # sideways wander
SNOW_SIZE    = (0.045, 0.11)


class Snow(Entity):
    def __init__(self):
        super().__init__(parent=city_root)
        self.flakes = []
        for _ in range(SNOW_COUNT):
            # Each flake wears one of the same four images as the sky, picked
            # at random and kept for the flake's whole life. Through the fog
            # they read as grain and colour rather than as pictures, which is
            # the Cruelty Squad trick - the texture is doing tone, not subject. - stole straight from cruelty squad anda n old doom mod that i found
            tex = (random.choice(sky_textures)
                   if (SNOW_TEXTURED and sky_textures) else None)
            f = Entity(parent=self, model='quad', billboard=True,
                       scale=random.uniform(*SNOW_SIZE),
                       texture=tex,
                       color=(RGB(255, 255, 255, random.randint(170, 245)) if tex
                              else RGB(235, 238, 245, random.randint(150, 235))),
                       unlit=True, double_sided=True)
            f.fall = random.uniform(*SNOW_FALL)
            f.phase = random.uniform(0, math.tau)
            self.flakes.append(f)
        self.seeded = False

    def seed(self):
        for f in self.flakes:
            f.position = Vec3(player.x + random.uniform(-SNOW_BOX / 2, SNOW_BOX / 2),
                              player.y + random.uniform(0, SNOW_TOP),
                              player.z + random.uniform(-SNOW_BOX / 2, SNOW_BOX / 2))
        self.seeded = True

    def update(self):
        if not city_root.enabled or game is None or game.state not in ('office', 'ending'):
            return
        if not self.seeded:
            self.seed()
        half = SNOW_BOX / 2
        for f in self.flakes:
            f.y -= f.fall * time.dt
            # a slow sideways wander, so it doesn't fall like rain
            f.phase += time.dt * 0.8
            f.x += math.sin(f.phase) * SNOW_DRIFT * time.dt
            # recycle: below your feet, or too far away, and it goes back up
            if (f.y < player.y - 2.0 or abs(f.x - player.x) > half
                    or abs(f.z - player.z) > half):
                f.position = Vec3(player.x + random.uniform(-half, half),
                                  player.y + SNOW_TOP,
                                  player.z + random.uniform(-half, half))

# Snow is built AFTER the sky textures below, because each flake wears one
# see the note in Snow.__init__. Look for 'snow = Snow()' further down.

# MORE SKIES, AND FASTER - CRAZY WEIRD SKY TEXTURES THAT MAKE NO SENSE IN THE VILLAGE
SKY_TEXTURES = [
    ['Enemy_MegafuckElite2'],
    ['Enemy_Security2'],
    ['Enemy_Orange'],
    ['ribcage'],
    ['red neck together'],
    ['guts'],
    ['menunaked'],
    ['watchtimeMEME'],             # WATCH TIME, overhead
    ['laterent'],                  # the rent notice, as weather
    ['cover_edit_heavy'],          # PUT YOUR FAITH IN THE MARKET
    ['nerves'],
    ['randomrainbow'],
    ['deathscreen3'],
    ['ArcadeCarpet'],
    ['store_control'],
]
SKY_SWAP_SECONDS = 0.5
# and how far each sky's tint is allowed to pull the fog away from Silent Hill
# grey. 1.0 is the old behaviour (fully that sky's palette), 0.0 is pure grey
# and no variation at all. 0.45 keeps the sick colours as a suggestion
# underneath the grey, which is what i was after.
SKY_TINT_STRENGTH = 0.20
# ONE FOG TINT PER SKY TEXTURE, in the same order as SKY_TEXTURES, so every
# picture drags its own sick palette over the whole village when it comes up.
# Deliberately unpleasant combinations rather than shades of grey.
SKY_FOG_TINTS = [ # small tints for a better look
    RGB(104, 106, 116),      # Enemy_MegafuckElite2
    RGB(86, 104, 88),        # Enemy_Security2
    RGB(126, 96, 78),        # Enemy_Orange
    RGB(112, 106, 96),       # ribcage
    RGB(118, 74, 70),        # red neck together
    RGB(104, 70, 64),        # guts
    RGB(96, 88, 112),        # menunaked
]

# THE SKY IS FOG-PROOF NOW. Two changes from before: it is small enough to sit
# inside the camera's new clip distance and it FOLLOWS THE PLAYER, so you are
# always standing in the middle of it; and setFogOff() below exempts it from
# scene fog entirely - which is the whole fix for the sky textures getting
# fogged out by the tint.


# so because of the tint i now completely overcomplicated the sky and its now a fog following the player insteda of just beign asolid pic in the sky
cemetery_sky = Entity(parent=city_root, model='sphere', scale=SKY_RADIUS * 2,
                      double_sided=True, color=color.white, unlit=True)
try:
    cemetery_sky.setFogOff(1)        # panda3d: this node ignores scene fog
    # DRAW IT FIRST and let it write no depth. A 68m sphere with the player
    # inside it covers every pixel on screen, and in the normal opaque bin
    # Panda3D may draw it after some of the village -  Free, and the cheapest full-screen fill there is, maybe perhaps idk tutorial said so.
    cemetery_sky.setBin('background', 0)
    cemetery_sky.setDepthWrite(False)
except Exception as e:
    print('!! could not exempt the sky from fog:', e)


def load_sky_textures():
    found, missing = [], []
    for names in SKY_TEXTURES:
        tex = None
        for n in names:
            tex = safe_texture(n + '_low') or safe_texture(n)
            if tex:
                found.append(tex)
                break
        if tex is None:
            missing.append(names[0])
    if missing:
        print('sky: could not find %s - put them anywhere in the project, or '
              'tell me the real filenames' % ', '.join(missing))
    print(f'sky: {len(found)} of {len(SKY_TEXTURES)} textures loaded')
    return found


sky_textures = load_sky_textures()
if sky_textures:
    cemetery_sky.texture = sky_textures[0]
else:
    cemetery_sky.color = FOG_VILLAGE_COLOR    # matches the fog, so the
                                             # horizon dissolves properly
class SkyCycler(Entity):
    def __init__(self):
        super().__init__()
        self.t = SKY_SWAP_SECONDS
        self.at = 0

    def update(self):
        if not city_root.enabled:
            return
        # the sky is centred on you every frame, so you can never walk toward
        # its edge and watch the picture get bigger - it behaves like a sky
        cemetery_sky.world_position = player.world_position
        if not sky_textures or len(sky_textures) < 2:
            return
        self.t -= time.dt
        if self.t > 0:
            return
        self.t = SKY_SWAP_SECONDS
        choices = [i for i in range(len(sky_textures)) if i != self.at]
        self.at = random.choice(choices)
        cemetery_sky.texture = sky_textures[self.at]
        # THE FOG TAKES ITS COLOUR FROM THE SKY, and changes with it. That is
        # what keeps the horizon from showing as a seam
        global FOG_VILLAGE_COLOR

        _t = SKY_FOG_TINTS[self.at % len(SKY_FOG_TINTS)]
        _g = SKY_FOG_TINTS[0]
        FOG_VILLAGE_COLOR = Vec4(lerp(_g[0], _t[0], SKY_TINT_STRENGTH),
                                 lerp(_g[1], _t[1], SKY_TINT_STRENGTH),
                                 lerp(_g[2], _t[2], SKY_TINT_STRENGTH), 1.0)
        t = FOG_VILLAGE_COLOR
        cemetery_sky.color = color.rgba(min(1, t[0] * 1.9), min(1, t[1] * 1.9),
                                        min(1, t[2] * 1.9), 1)


sky_cycler = SkyCycler()

snow = Snow()          # needs sky_textures, so it lives here disabled currently
cemetery_ambient = AmbientLight(parent=city_root, color=RGB(92, 96, 112))
cemetery_moon = DirectionalLight(parent=city_root, color=RGB(120, 128, 152),
                                 shadows=False)
cemetery_moon.look_at(Vec3(0.3, -1, 0.4))

wall_streamer = None            # the backrooms wall streamer went with them
still_life = None               # so did the thing that wandered in there, useless


def village_spawn_point():
    at = Vec3(OFFICE_ORIGIN_XZ.x, 0, OFFICE_ORIGIN_XZ.y) + SPAWN_OFFSET
    return Vec3(at.x, ground_under(at.x, at.z) + 0.25, at.z)


# kept under the old name so nothing else has to change
cemetery_spawn_point = village_spawn_point
angler_pickup = None # had a a different ide afor here

sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
# NPCS - villagers, walking, dialogue !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# THIS IS NO LONGER IN THE GAME THIS WAS SUPPOSED TO TRAVE LYOU T O AWHOLE NEWUNIVERSE BY TALKING TO HIS THIS IS WAY TOO MUCH
BENCH_GUY_SPLIT_FILES = True
BENCH_GUY_BENCH_OBJ = 'bench_only'
BENCH_GUY_MAN_OBJ   = 'man_only'
BENCH_GUY_OBJ    = 'mansitting'
BENCH_GUY_GLB    = 'after_work'
# THE MEN ON THE BENCHES ARE GONE, but ill keep he code cuz i have a new idea for it much later, cannot make it now
# BUT ALL OF THE TEXT DIALOGUES THEY HAD GIVEN TO OTHER VILLAGERS INSTEAD.
#
BENCH_GUY_COUNT  = 0        # was 3. See the note above.
BENCH_GUY_HEIGHT = 1.40
BENCH_GUY_TARGET = 'auto'

BENCH_GUY_YAW_OFFSET = 0

BENCH_GUY_SKIN_TEXTURE = 'afterwork_skin'
BENCH_GUY_FIXED = {
    'blob': (BENCH_GUY_SKIN_TEXTURE, color.white),
}

BENCH_GUY_DROP_MATERIALS = {'smoke2'}

BENCH_GUY_BENCH_WIDEN = 2.5
BENCH_GUY_BENCH_MATERIAL = 'bench1'    # which material IS the bench

BENCH_GUY_MAN_STRETCH = Vec3(1.45, 1.18, 1.25)

BENCH_GUY_X_RANGE = (-58.0, 8.0)     # along the road, past all five doors
BENCH_GUY_Z_SIDES = (3.4, -3.6)      # the two verges, either side of the road
BENCH_GUY_Z_JITTER = 0.7             # how far in and out he can wander
BENCH_GUY_MIN_GAP = 14.0             # metres between two of him
BENCH_GUY_CLEARANCE = 2.0            # metres he must be clear of any wall box
BENCH_GUY_SINK = 0.02                # pressed a hair into the ground, no gap

BENCH_GUY_SKINS = ['humanSUpremacy', 'memeface',
                   'ribcage', 'guts', 'nerves', 'red neck together',
                   'greenieface', 'greeter_face', 'eye 1', 'eye 2',
                   'black_hands 2', 'black_hands 3',
                   'Enemy_MegafuckElite2', 'Enemy_Security2', 'Enemy_Orange',
                   'randomrainbow', 'red_marble', 'crungewallpaper',
                   'purple_carpet', 'funko', 'doom_gun', 'easteregg_photo',
                   'grandma', 'grandma2', 'grandma3', 'menunaked',
                   'fulltemplate model', 'perfectbody', 'monthlysubscription',
                   'lifecourse', 'house100']
BENCH_GUY_TEX_SCALES = [(1, 1), (3, 2), (2, 5), (7, 3), (1, 4), (5, 5),
                        (11, 1), (2, 9)]

BENCH_GUY_INTERACT = 3.4
BENCH_GUY_SOLID_CAP = 2.4

BENCH_GUY_LINES = [
    [
        "Long day?",
        "I sit here after. Not for any reason. Just after.",
        "You get to the end of a shift and you find you have nowhere to be, "
        "and nobody minds either way.\n\nThat is the bit they do not warn "
        "you about. Not the work. The after.",
    ],
]
BENCH_GUY_NAME = 'AFTER WORK'
bench_guys = []          # every instance, so E and the watcher can find them
_bench_guy_parts = None

def read_bench_guy_geometry():
    global _bench_guy_parts
    if _bench_guy_parts is not None:
        return _bench_guy_parts

    if BENCH_GUY_SPLIT_FILES:
        bench_f = find_asset(f'{BENCH_GUY_BENCH_OBJ}.obj')
        man_f = find_asset(f'{BENCH_GUY_MAN_OBJ}.obj')
        if bench_f is not None and man_f is not None:
            try:
                merged = {}
                for f in (bench_f, man_f):
                    for mat, (v, u, _c) in load_obj_by_material(
                            f, flip_x=False, shade=False).items():
                        if v:
                            merged[mat] = (v, u)
                _bench_guy_parts = merged
                tris = sum(len(v) // 3 for v, _u in merged.values())
                print('bench guy: %s + %s read as separate files, %d materials '
                      '(%s), %d triangles'
                      % (bench_f.name, man_f.name, len(merged),
                         ', '.join(merged), tris))
                return _bench_guy_parts
            except Exception as exc:
                print('!! could not read the split bench/man files (%s) - '
                      'falling back to splitting %s by material'
                      % (exc, BENCH_GUY_OBJ))
        else:
            missing = [n for n, f in ((BENCH_GUY_BENCH_OBJ, bench_f),
                                      (BENCH_GUY_MAN_OBJ, man_f)) if f is None]
            print('   bench guy: %s.obj not found, splitting %s.obj by material '
                  'instead (same result)'
                  % ('/'.join(missing), BENCH_GUY_OBJ))

    obj = find_asset(f'{BENCH_GUY_OBJ}.obj')
    if obj is not None:
        try:
            groups = load_obj_by_material(obj, flip_x=False, shade=False)
            _bench_guy_parts = {mat: (v, u) for mat, (v, u, _c) in groups.items()
                                if v}
            tris = sum(len(v) // 3 for v, _u in _bench_guy_parts.values())
            print('bench guy: %s read, %d materials (%s), %d triangles'
                  % (obj.name, len(_bench_guy_parts),
                     ', '.join(_bench_guy_parts), tris))
            return _bench_guy_parts
        except Exception as exc:
            print('!! could not parse %s (%s) - trying the glb instead'
                  % (obj.name, exc))

    # fallback: the rigged .glb, bind pose, wrong proportions but present
    path = find_asset(f'{BENCH_GUY_GLB}.glb', f'{BENCH_GUY_GLB}.gltf')
    if path is None:
        print('!! neither %s.obj nor %s.glb found - the man on the bench will '
              'not appear. Put either one anywhere in the project.'
              % (BENCH_GUY_OBJ, BENCH_GUY_GLB))
        _bench_guy_parts = {}
        return _bench_guy_parts
    try:
        _bench_guy_parts = read_glb_by_material(path)
        tris = sum(len(v) // 3 for v, _u in _bench_guy_parts.values())
        print('bench guy: %s read (FALLBACK - he will look squashed, see the '
              'note on BENCH_GUY_OBJ), %d materials, %d triangles'
              % (path.name, len(_bench_guy_parts), tris))
    except Exception as exc:
        print('!! could not parse %s (%s) - no bench guy' % (path.name, exc))
        _bench_guy_parts = {}
    return _bench_guy_parts


def spot_is_clear(x, z, clearance):
    for cx, cz, sx, sz, _lo, _hi in village_wall_boxes:
        if (abs(x - cx) < sx / 2 + clearance
                and abs(z - cz) < sz / 2 + clearance):
            return False
    return True


def pick_bench_spots(count):
    spots = []
    for _try in range(600):
        if len(spots) >= count:
            break
        x = random.uniform(*BENCH_GUY_X_RANGE)
        z = random.choice(BENCH_GUY_Z_SIDES) + random.uniform(
            -BENCH_GUY_Z_JITTER, BENCH_GUY_Z_JITTER)
        if not spot_is_clear(x, z, BENCH_GUY_CLEARANCE):
            continue
        if any(math.hypot(x - sx, z - sz) < BENCH_GUY_MIN_GAP
               for sx, sz in spots):
            continue
        # and not on top of the office, or in the red door's way
        if math.hypot(x - OFFICE_ORIGIN_XZ.x, z - OFFICE_ORIGIN_XZ.y) < 9.0:
            continue
        if math.hypot(x - DOOM_DOOR_POS.x, z - DOOM_DOOR_POS.z) < 6.0:
            continue
        spots.append((x, z))
    if len(spots) < count:
        print('   (bench guy: only found %d clear roadside spots out of %d '
              'asked for - widen BENCH_GUY_X_RANGE or drop '
              'BENCH_GUY_CLEARANCE)' % (len(spots), count))
    return spots
_bench_guy_focus = None        #


def bench_guy_focus():
    global _bench_guy_focus
    if _bench_guy_focus is not None:
        return _bench_guy_focus
    parts = read_bench_guy_geometry()
    verts = [v for vl, _u in parts.values() for v in vl]
    if not verts:
        _bench_guy_focus = (0.0, 0.0)
        return _bench_guy_focus
    ys = [v[1] for v in verts]
    lo, hi = min(ys), max(ys)
    cut = lo + (hi - lo) * BENCH_GUY_FOCUS_TOP
    tall = [v for v in verts if v[1] >= cut]
    if not tall:
        tall = verts
    _bench_guy_focus = (sum(v[0] for v in tall) / len(tall),
                        sum(v[2] for v in tall) / len(tall))
    return _bench_guy_focus

BENCH_GUY_FOCUS_TOP = 0.55
BENCH_GUY_HEAD_FROM = 0.80
BENCH_GUY_HEAD_TURN = 62.0     # degrees either side before he gives up on you
BENCH_GUY_HEAD_SPEED = 1.9     # how fast the head tracks. Low = eerie.
BENCH_GUY_HEAD_RANGE = 11.0    # metres at which he starts noticing you

def bench_guy_neck(parts):
    man = [v for mat, (vl, _u) in parts.items() if mat not in BENCH_GUY_FIXED
           for v in vl]
    if not man:
        return 1e9, 0.0, 0.0            # no man: nothing gets split off
    ys = [v[1] for v in man]
    lo, hi = min(ys), max(ys)
    neck = lo + (hi - lo) * BENCH_GUY_HEAD_FROM
    head = [v for v in man if v[1] >= neck] or man
    return (neck,
            sum(v[0] for v in head) / len(head),
            sum(v[2] for v in head) / len(head))
_bench_guy_rigged_ok = None
BENCH_GUY_TRY_RIGGED = False


def try_rigged_bench_guy(inner, rng, index):
    global _bench_guy_rigged_ok
    try:
        rigged = Entity(parent=inner, model=BENCH_GUY_GLB, unlit=True,
                        double_sided=True)
        if rigged.model is None:
            destroy(rigged)
            _bench_guy_rigged_ok = False
            return False
        geoms = list(rigged.model.findAllMatches('**/+GeomNode')) or [rigged.model]
        for np_ in geoms:
            name = rng.choice(BENCH_GUY_SKINS)
            tex = crunchy_texture(None, name)
            if tex is None:
                print('!! bench guy texture missing: %s.png' % name)
                continue
            try:
                np_.setTexture(tex._texture, 1)
            except Exception:
                np_.setTexture(tex, 1)
        if _bench_guy_rigged_ok is None:
            print('   bench guy: loaded through ursina with its skeleton, '
                  '%d parts skinned' % len(geoms))
        _bench_guy_rigged_ok = True
        return True
    except Exception as exc:
        if _bench_guy_rigged_ok is None:      # say it once, not once per guy
            print('   bench guy: panda3d-gltf cannot read this rigged glb '
                  '(%s).' % exc)
            print('   bench guy: using the static bind pose instead - he sits '
                  'still rather than animating, everything else is identical. '
                  'This is expected, not a problem.')
        _bench_guy_rigged_ok = False
        return False


def build_bench_guy(index, spot):
    spot_x, spot_z = spot
    ground = village_ground(spot_x, spot_z) if village_ground else 0.0
    holder = Entity(parent=city_root,
                    position=Vec3(spot_x, ground - BENCH_GUY_SINK, spot_z))

    look = 0.0 if spot_z < 0 else 180.0
    holder.rotation_y = (look + BENCH_GUY_YAW_OFFSET) % 360

    inner = Entity(parent=holder)
    rng = random.Random(4200 + index)      # same guy, same skins, every run

    loaded = False
    if BENCH_GUY_TRY_RIGGED and _bench_guy_rigged_ok is not False:
        loaded = try_rigged_bench_guy(inner, rng, index)

    head_pivot = None
    if not loaded:
        parts = read_bench_guy_geometry()
        if not parts:
            destroy(holder)
            return None

        neck_y, head_x, head_z = bench_guy_neck(parts)

        for n, (mat, (vlist, ulist)) in enumerate(parts.items()):
            if not vlist:
                continue


            if mat in BENCH_GUY_DROP_MATERIALS:
                if index == 0:
                    print('   bench guy: material %r dropped (%d triangles) - '
                          'that is the cigarette' % (mat, len(vlist) // 3))
                continue
            pinned = BENCH_GUY_FIXED.get(mat)
            if pinned is not None:
                tex_name, tint = pinned
                tex = crunchy_texture(None, tex_name) if tex_name else None
                if tex_name and tex is None:
                    print('!! bench guy: %s.png missing - his skin falls back '
                          'to flat colour. Re-extract it from after_work.glb.'
                          % tex_name)

                body_v, body_u, head_v, head_u = [], [], [], []
                for t in range(0, len(vlist) - 2, 3):
                    mid_y = (vlist[t][1] + vlist[t + 1][1] + vlist[t + 2][1]) / 3.0
                    tgt_v, tgt_u = ((head_v, head_u) if mid_y >= neck_y
                                    else (body_v, body_u))
                    tgt_v.extend((vlist[t], vlist[t + 1], vlist[t + 2]))
                    tgt_u.extend((ulist[t], ulist[t + 1], ulist[t + 2]))

                if body_v:
                    piece = Entity(parent=inner,
                                   model=Mesh(vertices=body_v, uvs=body_u,
                                              mode='triangle', static=True),
                                   texture=tex, color=tint,
                                   double_sided=True, unlit=True)
                    piece.scale = BENCH_GUY_MAN_STRETCH
                if head_v:
                    if head_pivot is None:
                        head_pivot = Entity(parent=inner,
                                            position=Vec3(head_x, neck_y, head_z))
                        head_pivot.scale = BENCH_GUY_MAN_STRETCH
                    hv = [(v[0] - head_x, v[1] - neck_y, v[2] - head_z)
                          for v in head_v]
                    Entity(parent=head_pivot,
                           model=Mesh(vertices=hv, uvs=head_u,
                                      mode='triangle', static=True),
                           texture=tex, color=tint,
                           double_sided=True, unlit=True)
                if index == 0:
                    print('   bench guy: material %r keeps its ORIGINAL '
                          'texture (%s), stretched %s'
                          % (mat, tex_name, tuple(BENCH_GUY_MAN_STRETCH)))
                continue

            name = rng.choice(BENCH_GUY_SKINS)
            tex = crunchy_texture(None, name)
            if tex is None:
                print('!! bench guy texture missing: %s.png (material %s)'
                      % (name, mat))
            tint = color.white if tex else RGB(140, 130, 140)
            tscale = BENCH_GUY_TEX_SCALES[n % len(BENCH_GUY_TEX_SCALES)]

            body_v, body_u, head_v, head_u = [], [], [], []
            for t in range(0, len(vlist) - 2, 3):
                mid_y = (vlist[t][1] + vlist[t + 1][1] + vlist[t + 2][1]) / 3.0
                if mid_y >= neck_y:
                    head_v.extend((vlist[t], vlist[t + 1], vlist[t + 2]))
                    head_u.extend((ulist[t], ulist[t + 1], ulist[t + 2]))
                else:
                    body_v.extend((vlist[t], vlist[t + 1], vlist[t + 2]))
                    body_u.extend((ulist[t], ulist[t + 1], ulist[t + 2]))

            if body_v:
                piece = Entity(parent=inner,
                               model=Mesh(vertices=body_v, uvs=body_u,
                                          mode='triangle', static=True),
                               texture=tex, color=tint,
                               double_sided=True, unlit=True)
                piece.texture_scale = tscale

                if mat == BENCH_GUY_BENCH_MATERIAL:
                    piece.scale_x = BENCH_GUY_BENCH_WIDEN
                    if index == 0:
                        print('   bench guy: bench %r widened x%.1f - room for '
                              'other people on it now'
                              % (mat, BENCH_GUY_BENCH_WIDEN))
            if head_v:
                if head_pivot is None:
                    head_pivot = Entity(parent=inner,
                                        position=Vec3(head_x, neck_y, head_z))
                shifted = [(v[0] - head_x, v[1] - neck_y, v[2] - head_z)
                           for v in head_v]
                piece = Entity(parent=head_pivot,
                               model=Mesh(vertices=shifted, uvs=head_u,
                                          mode='triangle', static=True),
                               texture=tex, color=tint,
                               double_sided=True, unlit=True)
                piece.texture_scale = tscale
            if index == 0:
                print('   bench guy: material %r -> %s  (%d body tris, %d head '
                      'tris)' % (mat, name, len(body_v) // 3, len(head_v) // 3))

    try:
        b = inner.model.getTightBounds() if inner.model else None
    except Exception:
        b = None
    if b is None:
        try:
            b = inner.getTightBounds()
        except Exception:
            b = None
    centre = Vec3(0, 0.7, 0)
    size = Vec3(1.9, 1.4, 1.1)
    if b is not None:
        low, high = b[0], b[1]
        raw_h = max(0.001, high[1] - low[1])
        k = (BENCH_GUY_HEIGHT / raw_h if BENCH_GUY_TARGET == 'auto'
             else float(BENCH_GUY_TARGET))
        inner.scale = k
        inner.y = -low[1] * k

        cap = BENCH_GUY_SOLID_CAP
        fx, fz = bench_guy_focus()
        centre = Vec3(fx * k, (high[1] - low[1]) * k / 2, fz * k)
        size = Vec3(min(cap, (high[0] - low[0]) * k),
                    max(0.9, (high[1] - low[1]) * k),
                    min(cap, max(0.6, (high[2] - low[2]) * k)))
        if index == 0:
            print('   bench guy: measured %.2f x %.2f x %.2f units -> scale '
                  '%.4f, %.2fm tall at the head, bench %.1fm long'
                  % (high[0] - low[0], raw_h, high[2] - low[2], k,
                     raw_h * k, (high[0] - low[0]) * k))
            print('   bench guy: HE is at model x=%.2f z=%.2f (the tall part), '
                  'so the collider goes there' % (fx, fz))
            print('   bench guy: collider %.1f x %.1f x %.1fm centred (%.2f, '
                  '%.2f, %.2f)' % (size.x, size.y, size.z,
                                   centre.x, centre.y, centre.z))
    else:
        print('   !! could not measure the bench guy - he is at scale 1, so '
              'set BENCH_GUY_TARGET to a number if he is the wrong size')

    holder.collider = BoxCollider(holder, center=centre, size=size)

    holder.focus = Entity(parent=holder,
                          position=Vec3(centre.x, centre.y, centre.z))

    holder.head = head_pivot
    holder.is_bench_guy = True
    holder.guy_index = index

    holder.lines = (BENCH_GUY_LINES[index % len(BENCH_GUY_LINES)][:2]
                    + random_village_lines(seed=7000 + index))

    holder.talk_lines = holder.lines
    holder.talk_name = BENCH_GUY_NAME
    holder.talked = False
    bench_guys.append(holder)
    return holder


def build_bench_guys():
    if BENCH_GUY_COUNT <= 0:
        return
    if find_asset(f'{BENCH_GUY_OBJ}.obj', f'{BENCH_GUY_GLB}.glb',
                  f'{BENCH_GUY_GLB}.gltf') is None:
        print('!! neither %s.obj nor %s.glb found anywhere in the project - no '
              'man on the bench. Drop either next to launcher.py.'
              % (BENCH_GUY_OBJ, BENCH_GUY_GLB))
        return
    spots = pick_bench_spots(BENCH_GUY_COUNT)
    for i, spot in enumerate(spots):
        guy = build_bench_guy(i, spot)
        if guy is not None:
            print('   bench guy %d at (%.2f, %.2f, %.2f) facing %.0f'
                  % (i + 1, guy.x, guy.y, guy.z, guy.rotation_y))
    print('bench guys: %d sitting at the side of the road' % len(bench_guys))


build_bench_guys()


#ALL OF THIS IS REMOVED AND NO LOONGER IN THE GAME BUT I WANTED TO KEEP IT SO I CAN IMPROVE ON IT LATER ON THIS IDEA!!!!!!!!!!!!!!
#I ALREADY HAVE THE ASSETS FOR THE CHARACTERS AND MOST OF THE CODE


villagers = []                 # every villager, for E and the update loop
villager_cells = {}            # (ix, iz) -> ground height. THE NAVMESH.
villager_door_cells = []       # the cells that are outside a house door


def villager_cell_of(x, z):
    ix = int(math.floor(x / VILLAGER_CELL))
    iz = int(math.floor(z / VILLAGER_CELL))
    return (ix, iz)


def villager_world_of(cell):
    ix, iz = cell
    x = (ix + 0.5) * VILLAGER_CELL
    z = (iz + 0.5) * VILLAGER_CELL
    y = villager_cells.get(cell, 0.0)
    return Vec3(x, y, z)


def point_is_near_a_wall(x, z, clearance):
    for cx, cz, sx, sz, y_lo, y_hi in village_wall_boxes:
        half_x = sx / 2.0 + clearance
        half_z = sz / 2.0 + clearance
        if abs(x - cx) > half_x:
            continue
        if abs(z - cz) > half_z:
            continue
        return True
    return False


def build_villager_navmesh():
    villager_cells.clear()

    # WHERE THE EDGE OF THE VILLAGE IS. The collision file gets asked FIRST
    # and the model second, because the collision file is the thing that
    # decides where you can actually stand.
    edge = village_nav_bounds
    if edge is None:
        edge = village_bounds
    if edge is None:
        print('!! villagers: the village has no bounds - neither %s nor %s '
              'loaded - so there is no navmesh and nobody will walk'
              % (VILLAGE_NAV, VILLAGE_OBJ))
        return
    if village_ground is None:
        print('!! villagers: no village ground, so no navmesh and no walking')
        return

    x0, x1, z0, z1 = edge
    x0 = x0 + VILLAGER_EDGE_MARGIN
    x1 = x1 - VILLAGER_EDGE_MARGIN
    z0 = z0 + VILLAGER_EDGE_MARGIN
    z1 = z1 - VILLAGER_EDGE_MARGIN

    first_cell = villager_cell_of(x0, z0)
    last_cell = villager_cell_of(x1, z1)

    looked_at = 0
    for ix in range(first_cell[0], last_cell[0] + 1):
        for iz in range(first_cell[1], last_cell[1] + 1):
            looked_at += 1
            x = (ix + 0.5) * VILLAGER_CELL
            z = (iz + 0.5) * VILLAGER_CELL
            if x < x0 or x > x1:
                continue
            if z < z0 or z > z1:
                continue
            if point_is_near_a_wall(x, z, VILLAGER_CLEARANCE):
                continue
            villager_cells[(ix, iz)] = village_ground(x, z)

    print('villagers: %d walkable squares out of %d looked at, %.1fm each'
          % (len(villager_cells), looked_at, VILLAGER_CELL))
    keep_only_the_biggest_region()


def keep_only_the_biggest_region():
    if not villager_cells:
        return

    # find every region by flooding outwards from each unvisited square
    seen = set()
    regions = []
    for cell in villager_cells:
        if cell in seen:
            continue
        region = []
        stack = [cell]
        seen.add(cell)
        while stack:
            here = stack.pop()
            region.append(here)
            for other in villager_neighbours(here):
                if other in seen:
                    continue
                seen.add(other)
                stack.append(other)
        regions.append(region)

    biggest = regions[0]
    for region in regions:
        if len(region) > len(biggest):
            biggest = region

    thrown = len(villager_cells) - len(biggest)
    keep = {}
    for cell in biggest:
        keep[cell] = villager_cells[cell]
    villager_cells.clear()
    villager_cells.update(keep)

    print('villagers: %d separate regions found. Kept the biggest - %d '
          'squares, all reachable from each other - and dropped %d squares '
          'in %d cut-off pockets.'
          % (len(regions), len(biggest), thrown, len(regions) - 1))


def build_villager_door_list():
    del villager_door_cells[:]
    for house in village_houses:
        spot = house.get('outside')
        if spot is None:
            continue
        cell = villager_cell_of(spot.x, spot.z)
        if cell in villager_cells:
            villager_door_cells.append(cell)
            continue
        # the door step itself is usually too close to the wall to be a
        # walkable square, so I take the nearest one that is
        near = nearest_villager_cell(Vec3(spot))
        if near is not None:
            villager_door_cells.append(near)
    print('villagers: %d house doors to visit' % len(villager_door_cells))


def nearest_villager_cell(pos):
    start = villager_cell_of(pos.x, pos.z)
    if start in villager_cells:
        return start
    for ring in range(1, 25):
        best = None
        best_gap = 1e9
        for ix in range(start[0] - ring, start[0] + ring + 1):
            for iz in range(start[1] - ring, start[1] + ring + 1):
                # only the edge of the ring - the inside was checked already
                on_edge = (abs(ix - start[0]) == ring
                           or abs(iz - start[1]) == ring)
                if not on_edge:
                    continue
                if (ix, iz) not in villager_cells:
                    continue
                here = villager_world_of((ix, iz))
                gap = distance(here, pos)
                if gap < best_gap:
                    best = (ix, iz)
                    best_gap = gap
        if best is not None:
            return best
    return None


def villager_neighbours(cell):
    ix, iz = cell
    here_y = villager_cells[cell]
    out = []
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        other = (ix + dx, iz + dz)
        if other not in villager_cells:
            continue
        if abs(villager_cells[other] - here_y) > VILLAGER_MAX_SLOPE:
            continue          # too steep to walk up. It is a bank, not a path. - so i made the whole village pretty much one
            # height
        out.append(other)
    return out


def find_villager_route(start, goal):
    if start not in villager_cells:
        return None
    if goal not in villager_cells:
        return None
    if start == goal:
        return [goal]

    came_from = {start: None}
    queue = [start]
    read_at = 0

    while read_at < len(queue):
        cell = queue[read_at]
        read_at += 1
        if cell == goal:
            break
        for other in villager_neighbours(cell):
            if other in came_from:
                continue
            came_from[other] = cell
            queue.append(other)

    if goal not in came_from:
        return None

    route = []
    cell = goal
    while cell is not None:
        route.append(cell)
        cell = came_from[cell]
    route.reverse()
    return route


def pick_villager_destination(from_cell):
    want_a_door = random.random() < VILLAGER_DOOR_CHANCE
    if want_a_door and villager_door_cells:
        return random.choice(villager_door_cells)
    if not villager_cells:
        return None
    # a plain random square. Not far away on purpose - a villager crossing
    # the entire village looks like an errand, not like living somewhere.
    for _try in range(30):
        cell = random.choice(list(villager_cells.keys()))
        if cell == from_cell:
            continue
        gap = abs(cell[0] - from_cell[0]) + abs(cell[1] - from_cell[1])
        if gap < 4:
            continue          # too close to be worth walking to  bruh
        if gap > 30:
            continue
        return cell
    return None


# your models have no bones, so the triangles are sorted into six piles

#THIS IS AIIIIIIIIIIIII, BECAUSE I DIDNT KNOW YET HOW TO RIG ASSETS IN BELDNER WHICH I FORTUNATELY HAVE NOW FIGUERED OUT
#BUT HERE I THOUGHT THIS WAS THE ONLY WAY TO GET IT DONE, AND NOW THEY ARE LIKE THIS

def which_limb(centre, rig):
    x, y, _z = centre
    if y > rig['head_y']:
        return 'head'
    if y < rig['hip_y']:
        return 'lleg' if x < rig['leg_split_x'] else 'rleg'
    if x < -rig['arm_x']:
        return 'larm'
    if x > rig['arm_x']:
        return 'rarm'
    return 'body'


def limb_joint(part, rig):
    if part == 'larm':
        return (-rig['arm_x'], rig['shoulder_y'], 0.0)
    if part == 'rarm':
        return (rig['arm_x'], rig['shoulder_y'], 0.0)
    if part == 'lleg':
        return (rig['leg_split_x'] - 0.06, rig['hip_y'], 0.0)
    if part == 'rleg':
        return (rig['leg_split_x'] + 0.06, rig['hip_y'], 0.0)
    return (0.0, 0.0, 0.0)


def build_walking_body(holder, model_name, rig, head_tex, body_tex,
                       target_height=NPC_TARGET_HEIGHT):
    path = find_asset(model_name + '.obj')
    if path is None:
        return None
    try:
        groups = load_obj_by_material(path, flip_x=False, shade=False)
    except Exception as exc:
        print('!! could not read %s.obj for the walk cycle (%s)'
              % (model_name, exc))
        return None
    if not groups:
        return None

    # measure it, so the scale is never a guess
    all_y = []
    for _mat, (vlist, _u, _c) in groups.items():
        for v in vlist:
            all_y.append(v[1])
    if not all_y:
        return None
    low, high = min(all_y), max(all_y)
    tall = max(0.001, high - low)
    scale = target_height / tall

    # ONE NODE THAT TURNS THE WHOLE PERSON ROUND
    facing = Entity(parent=holder,
                    rotation_y=VILLAGER_MODEL_YAW.get(model_name, 0))

    piles = {}
    for mat, (vlist, ulist, _clist) in groups.items():
        for i in range(0, len(vlist) - 2, 3):
            a, b, c = vlist[i], vlist[i + 1], vlist[i + 2]
            centre = ((a[0] + b[0] + c[0]) / 3.0,
                      (a[1] + b[1] + c[1]) / 3.0,
                      (a[2] + b[2] + c[2]) / 3.0)
            part = which_limb(centre, rig)
            key = (part, mat)
            if key not in piles:
                piles[key] = ([], [])
            piles[key][0].extend((a, b, c))
            piles[key][1].extend((ulist[i], ulist[i + 1], ulist[i + 2]))

    def measure_joint(part):
        got = []
        for (p, _m), (vl, _ul) in piles.items():
            if p == part:
                got.extend(vl)
        if not got:
            return limb_joint(part, rig)     # nothing there: fall back
        top = max(v[1] for v in got)
        band = max(0.02, (top - min(v[1] for v in got)) * 0.18)
        near_top = [v for v in got if v[1] >= top - band] or got
        cx = sum(v[0] for v in near_top) / len(near_top)
        cz = sum(v[2] for v in near_top) / len(near_top)
        return (cx, top, cz)

    # build one Entity per pile, under a pivot at its joint
    pivots = {}
    joints = {}
    for part in ('larm', 'rarm', 'lleg', 'rleg'):
        jx, jy, jz = measure_joint(part)
        joints[part] = (jx, jy, jz)
        pivots[part] = Entity(parent=facing,
                              position=Vec3(jx * scale,
                                            (jy - low) * scale,
                                            jz * scale))

    made = 0
    for (part, mat), (vlist, ulist) in piles.items():
        if not vlist:
            continue
        # THIS WAS A VERY ANNOYING BUG WHICH I HAD TO FIX MYSELF IN BLENDER AFTER ALL, joint sits at the origin of its pivot:
        # so when i ut them with this script/code up from here
        if part in pivots:
            parent = pivots[part]
            jx, jy, jz = joints[part]     # the MEASURED joint, see above
        else:
            parent = facing
            jx, jy, jz = 0.0, low, 0.0

        moved = []
        for v in vlist:
            moved.append(((v[0] - jx) * scale,
                          (v[1] - low - (jy - low)) * scale,
                          (v[2] - jz) * scale))
        want_tex = head_tex if part == 'head' else body_tex
        tex = crunchy_texture(None, want_tex) if want_tex else None
        Entity(parent=parent,
               model=Mesh(vertices=moved, uvs=ulist, mode='triangle',
                          static=True),
               texture=tex,
               color=color.white if tex else RGB(190, 180, 170),
               double_sided=True, unlit=True)
        made += 1

    if made == 0:
        return None
    return pivots


class Villager(Entity):
    def __init__(self, spec, start_cell, index=0):
        super().__init__(parent=city_root)
        self.spec = spec
        self.index = index
        self.position = villager_world_of(start_cell)

        #WHICH MODEL, AND HOW TALL
        # I wanted all of them to have random textures and random models from
        # the ones i had made. A spec with no 'model' gets one at random from
        # VILLAGER_RIGS - which is the list of models i know how to cut into
        # limbs, so a random pick can never land on something that cannot walk.

        pick = random.Random(7000 + index)
        model_name = spec.get('model')
        if not model_name:

            model_name = pick.choice(VILLAGER_MODEL_POOL)
        self.height = spec.get('height')
        if not self.height:
            self.height = pick.choice(VILLAGER_HEIGHTS)
        # WHICH CLOTHES THIS ONE WEARS
        # Seeded from the villager's own index, so it is decided once and
        # is the same every launch - "not random every time", which is what i want.

        dice = random.Random(4000 + index)
        head_tex = VILLAGER_HEAD_TEXTURES.get(model_name)
        own_body = VILLAGER_OWN_BODY_TEXTURES.get(model_name)

        dealt = spec.get('_dealt_texture')
        if spec.get('rich'):
            # THE RICH ONES. rich=True in VILLAGERS means "wear the texture
            # that came with the model", so they are the only people on the
            # street who look the way I intended. Everybody else is in
            # brick, offal or wallpaper.
            body_tex = own_body
        elif dealt:
            body_tex = dealt             # nobody else is wearing this one
        elif VILLAGER_BODY_TEXTURES:
            body_tex = dice.choice(VILLAGER_BODY_TEXTURES)
        else:
            body_tex = own_body
        self.is_rich = bool(spec.get('rich'))
        # WHOSE VOICE. A fixed one from the spec if it has one, otherwise
        # None for now - build_villagers() deals the rotating recordings out
        # afterwards, once it knows who is left. talk_to_npc() reads this.
        self.talk_voice = spec.get('voice')

        # the model, cut into limbs
        self.limbs = None
        rig = VILLAGER_RIGS.get(model_name)
        if VILLAGER_WALK_ANIM and rig is not None:
            self.limbs = build_walking_body(self, model_name, rig,
                                            head_tex, body_tex,
                                            target_height=self.height)
        got = self.limbs
        if got is None and model_name:
            # no rig for this model, or the .obj would not read
            got = fit_npc_model(self, model_name)
        if got is None:
            print('!! villager %r: could not load %r - placeholder standing in'
                  % (spec.get('name'), model_name))
            build_placeholder_npc(self)

        # the walk cycle's own state!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        self.stride_phase = dice.uniform(0, 6.283)

        self.swing_amount = 0.0     # 0 standing, 1 walking. Eased, so limbs
                                    # settle instead of snapping to a stop.

        # WHAT MAKES E WORK ON THEM.
        # These are the SAME five attributes the house NPCs carry. That is not
        # a coincidence, it is the whole reason a villager needs no new
        # interaction code: do_interact() looks for talk_lines and nothing
        # else, and talk_to_npc() does the rest.
        self.is_npc = True
        self.is_villager = True
        self.talk_name = spec.get('name', '')
        self.talk_lines = list(spec.get('lines', []))
        self.talked = False
        self.npc_room = None
        # the box you point at follows their real height, so a child is a
        # child-sized target and a tall one is a tall target

        #this actually doesnt really work but i never fixed it
        self.collider = BoxCollider(self,
                                    center=Vec3(0, self.height / 2, 0),
                                    size=Vec3(0.75, self.height, 0.75))

        # the wandering
        self.route = []
        self.route_at = 0
        # staggered, so thirty-nine of them never all decide where to go
        # on the same frame - that is 39 route searches at once and it is
        # a visible hitch. See VILLAGER_THINK_SPREAD.
        self.idle_left = (random.uniform(VILLAGER_IDLE_MIN, VILLAGER_IDLE_MAX)
                          + index * VILLAGER_THINK_SPREAD)
        self.leg_time = 0.0
        self.lod_wait = 0.0
        self.lod_dt = 0.0
        self.far_away = False
        villagers.append(self)

    def my_cell(self):
        return villager_cell_of(self.x, self.z)

    def am_i_talking(self):
        if not talk_box.open:
            return False
        return talk_box.speaker is self

    def start_idling(self):
        self.route = []
        self.route_at = 0
        self.idle_left = random.uniform(VILLAGER_IDLE_MIN, VILLAGER_IDLE_MAX)


    # THE WALK CYCLE FOR VILLAGERS

    def swing_limbs(self, walked_metres):
        if not self.limbs:
            return

        # how far through the stride we are
        if walked_metres > 0:
            # stride scales with leg length!!!!!!!!!!!!!!!!!, so a child takes quick short
            # steps and a tall one takes long slow ones - without either of
            # them sliding, because the phase still advances with DISTANCE
            stride = VILLAGER_STRIDE * (self.height / NPC_TARGET_HEIGHT)
            self.stride_phase += (walked_metres / max(0.05, stride)) * 6.283

        # Ease the swing in when they set off and out when they stop, so
        # nobody freezes mid-step with a leg in the air.


        # FAR AWAY: do not animate the limbs at all. Four rotations a frame
        # each, times however many are off in the distance, for something 30
        # metres away in fog - not worth a single one of them.
        if getattr(self, 'far_away', False):
            return
        want = 1.0 if walked_metres > 0.0005 else 0.0
        self.swing_amount = lerp(self.swing_amount, want,
                                 min(1, time.dt * VILLAGER_SWING_EASE))
        if self.swing_amount < 0.002 and want == 0.0:
            self.swing_amount = 0.0

        wave = math.sin(self.stride_phase) * self.swing_amount
        leg = wave * VILLAGER_LEG_SWING
        arm = wave * VILLAGER_ARM_SWING

        self.limbs['lleg'].rotation_x = leg
        self.limbs['rleg'].rotation_x = -leg
        self.limbs['larm'].rotation_x = -arm
        self.limbs['rarm'].rotation_x = arm

    def choose_somewhere_to_go(self):
        here = self.my_cell()
        if here not in villager_cells:
            # they have somehow ended up off the mesh - put them back on it. FAILSAFE PRETTY MUCH
            # This should never happen; it is here so that if it ever does,
            # it fixes itself instead of leaving somebody stood in a wall.
            back = nearest_villager_cell(self.world_position)
            if back is None:
                return
            self.position = villager_world_of(back)
            here = back

        goal = pick_villager_destination(here)
        if goal is None:
            self.start_idling()
            return

        route = find_villager_route(here, goal)
        if route is None:
            self.start_idling()
            return

        self.route = route
        self.route_at = 1 if len(route) > 1 else 0
        self.leg_time = 0.0

    def walk_towards(self, target):
        to_there = target - self.world_position
        to_there.y = 0
        gap = to_there.length()
        if gap < 0.001:
            return 0.0
        # lod_dt is time.dt when you are near and the whole missed
        # interval when you are far - so a distant villager covers the
        # same ground in fewer, bigger steps. See VILLAGER_LOD_ON. - ANOTHER AMAZING FEATURE


        #THIS SPECIFIC ONLY THIS SPECIFIC FEATURE WAS RECOMMENDED TO ME BY AI BECAUSE IT HELPS WITH A BIT OF OPITMISATION FOR THE GAME.


        step = to_there.normalized() * VILLAGER_SPEED * self.lod_dt
        if step.length() > gap:
            step = to_there
        self.x = self.x + step.x
        self.z = self.z + step.z
        # THE GROUND. village_ground() is the same baked height lookup the
        # player stands on, so a villager walking up the slope by the shop goes
        # up it, and one crossing a kerb steps over it. This is also why they
        # can never sink into or float above the road.
        self.y = village_ground(self.x, self.z) + VILLAGER_BOB * abs(
            math.sin(self.stride_phase)) if VILLAGER_BOB else village_ground(
            self.x, self.z)

        want = math.degrees(math.atan2(to_there.x, to_there.z))
        self.rotation_y = lerp_angle(self.rotation_y, want,
                                     min(1, self.lod_dt * VILLAGER_TURN_SPEED))
        # how far they actually moved, for the stride phase
        self.walked_this_frame = math.hypot(step.x, step.z)
        return gap

    def update(self):
        if not VILLAGERS_ON:
            return
        if game is None or game.state != 'office':
            return
        if not city_root.enabled:
            return
        if _menu_open or application.paused:
            return

        # LEVEL OF DETAIL VERY IMPORTANT !!!!!!!!!!!!!!!

        # See VILLAGER_LOD_ON. Far-away villagers get updated every
        # VILLAGER_LOD_STEP seconds instead of every frame, and the time they
        # missed is handed to walk_towards() so they cover the same distance.
        # Near ones are untouched.
        self.lod_wait = getattr(self, 'lod_wait', 0.0)
        self.lod_dt = time.dt
        if VILLAGER_LOD_ON:
            # THE LOD CHECK WAS COSTING MORE THAN THE LOD SAVED
            # Three changes, none of which alter a villager's behaviour:
            #   1. the player position comes from player_pos(), computed once
            #      a frame for the whole game - AND ONLY FROM THERE
            #   2. squared distance, so no square root - comparing against
            #      VILLAGER_LOD_NEAR squared is the same test!!
            self.lod_check = getattr(self, 'lod_check', 0.0) - time.dt
            if self.lod_check <= 0:
                self.lod_check = VILLAGER_LOD_RECHECK * random.uniform(0.7, 1.3)
                here = self.world_position
                there = player_pos()
                dx = here.x - there.x
                dz = here.z - there.z
                dy = here.y - there.y
                self.far_away = (dx * dx + dy * dy + dz * dz) > VILLAGER_LOD_NEAR_SQ
            if self.far_away:
                self.lod_wait += time.dt
                if self.lod_wait < VILLAGER_LOD_STEP:
                    return
                self.lod_dt = self.lod_wait
                self.lod_wait = 0.0
            else:
                self.lod_dt = time.dt
                self.lod_wait = 0.0

        #DEAD VILLAGERS - I HAVE NOW AFTER PLAY TESTIGNWITH FRIEND REALISED THAT PEOPLE DON'T EVEN FIGURE OUT THAT YOU CAN KILL
        #VILLAGE NPCS
        # when a villager dies they fall over, stay there and then disappear. without this the corpse carried on walking its route while lying on its side
        if getattr(self, 'dead', False):
            return

        # nothing moved yet this frame
        self.walked_this_frame = 0.0

        # TALKING. They stand still and let the dialogue camera turn them.
        # once you interact with them they stop, and they carry on walking after the conversation
        if self.am_i_talking():
            self.swing_limbs(0.0)      # limbs ease back to standing
            return

        # IDLING.
        if not self.route:
            self.swing_limbs(0.0)
            self.idle_left -= self.lod_dt
            if self.idle_left <= 0:
                self.choose_somewhere_to_go()
            return

        # WALKING.
        if self.route_at >= len(self.route):
            self.start_idling()
            return

        target = villager_world_of(self.route[self.route_at])
        gap = self.walk_towards(target)
        self.swing_limbs(self.walked_this_frame)

        self.leg_time += self.lod_dt
        if self.leg_time > VILLAGER_REPATH_SECONDS:
            # anotherfailsafe cuz when villagers fail its extreamly funny One leg is 2 metres and they walk at 1.25 m/s, so
            # a leg takes under two seconds - six means something is wrong,
            # and the cure is simply to think again, like a hard reset
            self.choose_somewhere_to_go()
            return

        if gap <= VILLAGER_ARRIVE:
            self.route_at += 1
            self.leg_time = 0.0
            if self.route_at >= len(self.route):
                self.start_idling()

# WHERE THEY GO, AND WHY NOTHING LANDS IN A WALL
STREET_PROPS_ON = True
# Where the road runs, on Z. Taken from BENCH_GUY_Z_SIDES so the code is still useful a bit even though its not being used, which is the pair
# of verges the old bench men stood on - (3.4, -3.6), so the middle of the
# road is about -0.1. Everything below measures "how far off the road" from
# here.
STREET_CENTRE_Z = -0.1

BENCH_GLB     = 'bench'
BENCH_COUNT   = 7          # "maybe 6-7"
BENCH_HEIGHT  = 1.00       # metres tall. It is 1.00 in its own units already.
BENCH_EDGE    = 4.0        # how far from the middle of the road they sit
BENCH_SOLID   = True       # you cannot walk through them


# SO THE TREEEEEEEEEEEEEEEES ARE GENERATED
TREE_TRUNK_TEXTURE = 'darkwood'      # bark
TREE_LEAF_TEXTURE  = 'terrain_grass' # canopy
TREE_TRUNK_TINT    = RGB(125, 100, 70)
TREE_LEAF_TINT     = RGB(120, 165, 95)
# How many times each image repeats. Bigger = smaller, busier pattern.
TREE_BARK_AROUND   = 2.0    # times around the trunk
TREE_BARK_UP       = 4.0    # times up its height
TREE_LEAF_TILES    = 0.9    # repeats per metre across the canopy

# The third entry is now HOW to texture it, not just which image:
TREE_MODELS   = [
    # (file, how tall in metres, how many, how to texture)
    ('trees_low_poly',      9.0,  10, None),
    ('giant_low_poly_tree', 14.0,  4, 'uv'),
]
# kept for the old path only - trees_low_poly is not tinted
TREE_TINT = RGB(120, 150, 105)
TREE_EDGE_MIN = 7.0        # trees start this far out from the road centre,
                           # so they never grow through the street itself
TREE_APART    = 9.0        # metres between two trees
TREE_SOLID    = True
TREE_TRUNK    = 0.9        # the collider is a trunk, not the whole canopy -
                           # you can walk under the branches


def make_tree_uvs(verts, kind):
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    mid_x = (min(xs) + max(xs)) / 2.0
    mid_z = (min(zs) + max(zs)) / 2.0
    low = min(ys)
    span = (max(ys) - low) or 1.0

    uvs = []
    if kind == 'cylinder':
        for i in range(0, len(verts) - 2, 3):
            us, vs = [], []
            for v in verts[i:i + 3]:
                angle = math.atan2(v[2] - mid_z, v[0] - mid_x)
                us.append((angle / (2 * math.pi) + 0.5) * TREE_BARK_AROUND)
                vs.append((v[1] - low) / span * TREE_BARK_UP)
            # THE SEAM # THIS IS AI, AND FOR THIS I CANT EVEN EXPLAIN IT ITS SOMETHING WITH UI-S AND I HAD NO TIME TO GET THIS RIGHT
            # atan2 jumps from +pi to -pi at the back of the trunk. A triangle
            # with one corner either side of that jump gets UVs like 0.02 and
            # 1.98, so the texture gets drawn stretched backwards across the
            # entire trunk in one ugly band. If a triangle spans more than half
            # the wrap it must be a seam one, so push its low corners around by
            # a full turn instead.
            if max(us) - min(us) > TREE_BARK_AROUND * 0.5:
                us = [u + TREE_BARK_AROUND if u < TREE_BARK_AROUND * 0.5 else u
                      for u in us]
            uvs.extend(zip(us, vs))
    else:
        for i in range(0, len(verts) - 2, 3):
            a, b, c = verts[i], verts[i + 1], verts[i + 2]
            # face normal, by cross product of two edges
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            wx, wy, wz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx = abs(uy * wz - uz * wy)
            ny = abs(uz * wx - ux * wz)
            nz = abs(ux * wy - uy * wx)
            for v in (a, b, c):
                if nx >= ny and nx >= nz:      # mostly facing left/right
                    p, q = v[2], v[1]
                elif ny >= nx and ny >= nz:    # mostly facing up/down
                    p, q = v[0], v[2]
                else:                          # mostly facing front/back
                    p, q = v[0], v[1]
                uvs.append((p * TREE_LEAF_TILES, q * TREE_LEAF_TILES))
    return uvs


def build_textured_tree(parent, path):
    try:
        groups = read_glb_by_material(path)
    except Exception as exc:
        print('!! could not read the big tree: %s' % exc)
        return None
    if not groups:
        return None

    bark = crunchy_texture(None, TREE_TRUNK_TEXTURE)
    leaf = crunchy_texture(None, TREE_LEAF_TEXTURE)

    body = Entity(parent=parent)
    made = 0
    for material, (verts, _ignored_uvs) in groups.items():
        if len(verts) < 3:
            continue
        wood = 'wood' in material.lower() or 'trunk' in material.lower()
        uvs = make_tree_uvs(verts, 'cylinder' if wood else 'triplanar')
        Entity(parent=body,
               model=Mesh(vertices=list(verts), uvs=uvs,
                          mode='triangle', static=True),
               texture=bark if wood else leaf,
               color=TREE_TRUNK_TINT if wood else TREE_LEAF_TINT,
               unlit=True, double_sided=True)
        made += 1
    if not made:
        destroy(body)
        return None
    return body


def place_street_props():
    if not STREET_PROPS_ON:
        return
    if not villager_cells:
        print('!! no navmesh, so no benches or trees')
        return

    taken = []

    def far_enough(spot, gap):
        for other in taken:
            if distance(spot, other) < gap:
                return False
        return True

    def spots_between(low, high, count, gap, seed):
        dice = random.Random(seed)
        cells = list(villager_cells.keys())
        dice.shuffle(cells)
        out = []
        for cell in cells:
            if len(out) >= count:
                break
            if cell in villager_door_cells:
                continue          # never in front of somebody's door
            here = villager_world_of(cell)
            # ROAD_CENTRE_Z is where the street runs; the houses are north
            # and south of it. abs(z) is therefore "how far off the road".
            off = abs(here.z - STREET_CENTRE_Z)
            if off < low or off > high:
                continue
            if not far_enough(here, gap):
                continue
            taken.append(here)
            out.append(here)
        return out

    # the benches
    made = 0
    bench_path = find_asset(BENCH_GLB + '.glb')
    if bench_path is None:
        print('!! %s.glb not found - no benches' % BENCH_GLB)
    else:
        for spot in spots_between(BENCH_EDGE - 2.5, BENCH_EDGE + 2.5,
                                  BENCH_COUNT, 6.0, 4242):
            holder = Entity(parent=city_root, position=spot)
            body = Entity(parent=holder, model=BENCH_GLB, unlit=True,
                          double_sided=True)
            if body.model is None:
                destroy(holder)
                continue
            fit_prop(body, holder, BENCH_HEIGHT)
            # face the road, so they are benches you would sit on to watch
            # the street rather than benches facing a wall
            holder.rotation_y = 0 if spot.z > STREET_CENTRE_Z else 180
            if BENCH_SOLID:
                # MEASURED, NOT TYPED
                # They had one, but it was a hardcoded 2.0 x 1.0 x 0.7 box
                try:
                    lo, hi = body.getTightBounds(holder)
                    bw = max(0.4, hi[0] - lo[0])
                    bh = max(0.4, hi[1] - lo[1])
                    bd = max(0.3, hi[2] - lo[2])
                    Entity(parent=holder, model='cube', collider='box',
                           visible=False,
                           position=((lo[0] + hi[0]) / 2,
                                     (lo[1] + hi[1]) / 2,
                                     (lo[2] + hi[2]) / 2),
                           scale=(bw, bh, bd))
                except Exception:
                    # the old fixed box, if the bounds cannot be read
                    Entity(parent=holder, model='cube', collider='box',
                           visible=False, position=(0, 0.5, 0),
                           scale=(2.0, 1.0, 0.7))
            made += 1
    print('street: %d benches' % made)

    # the trees
    grown = 0
    for name, tall, count, skin in TREE_MODELS:
        path = find_asset(name + '.glb')
        if path is None:
            print('!! %s.glb not found - those trees are missing' % name)
            continue
        for spot in spots_between(TREE_EDGE_MIN, 60.0, count, TREE_APART,
                                  hash(name) % 9999):
            holder = Entity(parent=city_root, position=spot,
                            rotation=(0, random.uniform(0, 360), 0))
            if skin == 'uv':
                # no UVs in the file, so it is rebuilt with
                # generated ones rather than loaded flat. See TREE_MODELS.
                body = build_textured_tree(holder, path)
                if body is None:
                    destroy(holder)
                    continue
            else:
                body = Entity(parent=holder, model=name, unlit=True,
                              double_sided=True)
                if body.model is None:
                    destroy(holder)
                    continue
                if skin:
                    got = crunchy_texture(None, skin)
                    if got is not None:
                        body.texture = got
                        body.color = TREE_TINT
                    else:
                        print('!! tree texture %r not found' % skin)
            fit_prop(body, holder, tall)
            if TREE_SOLID:
                # A TRUNK, not the canopy. A collider round the whole tree
                # would be an invisible wall ten metres across that you
                # cannot see the edge of - this is a post you walk around.
                Entity(parent=holder, model='cube', collider='box',
                       visible=False, position=(0, tall / 2, 0),
                       scale=(TREE_TRUNK, tall, TREE_TRUNK))
            grown += 1
    print('street: %d trees' % grown)


def fit_prop(body, holder, target_height):
    try:
        b = body.getTightBounds(holder)
        h = (b[1][1] - b[0][1]) or 1.0
        body.scale = target_height / h
        b2 = body.getTightBounds(holder)
        body.y -= b2[0][1]
    except Exception as exc:
        print('!! could not measure a street prop (%s)' % exc)


# WHY THE FRAME RATE WAS A PROBLEM - THIS SHOULD ROUGHLY LAY IT OUT, TO THE BEST OF MY EXPLANATION

#
#     for entitiy in scene.entities:
#         if not entitiy.enabled or entitiy.ignore:      <- cheap, and it EXITS here
#             continue
#         if application.paused and ...:
#             continue
#         if entitiy.has_disabled_ancestor():      <- WALKS UP THE PARENT CHAIN
#             continue
#         if hasattr(e, 'update') and callable(e.update):
#             entity.update()
#
# EVERY entity in the game goes through IF ITS ENABLED, SHOULD CONTINUE, IS PAUSED, OR CALLABLE IN A CHAIN , every frame, whether it does
# anything or not. A wall does not move, but the engine still asks it four questions

# This game has thousands of entities: 996 village wall boxes, the village cut
# into chunks, five house interiors, 39 villagers with six limb meshes each,
# the DOOM map by material, trees, benches, adverts, the HUD. The per-frame
# cost of that loop is real and it gets paid before a single triangle is drawn.
#

#W HAT I CANT DO AND WHAT ARE MY OPTIONS ROUGHLY
# They keep STATIC and DYNAMIC objects in separate lists and never walk the
# static one. Ursina has no such split - but it has `ignore`, and the loop
# tests it FIRST, before the ancestor walk. So marking a static prop
# ignore=True is exactly that split: the entity still draws, still collides,
# and gets skipped by the update loop in one comparison.

#lowk just whether you ask or you skip


#IMPORTENTOOOOOOOOOO
# Anything with an update() of its own, anything that handles input, every
# Button and every Text. Those get found and left alone rather than listed by
# hand, so nothing can be frozen by accident when i add something new!!!!!!!!!!!!!!!!!!!!!!!!!
OPTIMISE_STATIC = True
OPTIMISE_REPORT = True      # print how many were frozen


def freeze_static_entities():
    if not OPTIMISE_STATIC:
        return 0
    frozen = 0
    looked = 0
    for e in list(scene.entities):
        looked += 1
        try:
            if e.ignore:
                continue                      # already out of the loop
            # anything that does something per frame, or reacts to you
            if hasattr(e, 'update') and callable(getattr(e, 'update', None)):
                continue
            if hasattr(e, 'input') and callable(getattr(e, 'input', None)):
                continue
            if hasattr(e, 'on_click') and e.on_click is not None:
                continue
            if isinstance(e, (Button, Text)):
                continue
            if e is player or e is camera or e is scene:
                continue
            if getattr(e, 'scripts', None):
                continue                      # a script needs the loop
            e.ignore = True
            frozen += 1
        except Exception:
            continue
    if OPTIMISE_REPORT:
        print('optimise: %d of %d entities frozen out of the update loop'
              % (frozen, looked))
    return frozen


def build_villagers():
    if not VILLAGERS_ON:
        print('villagers: VILLAGERS_ON is False - the village is empty')
        return
    adopt_bench_dialogue()
    hand_out_textures()      # before anybody is built - it reads it
    build_villager_navmesh()
    if not villager_cells:
        print('!! villagers: nowhere walkable was found, so nobody is placed')
        return
    build_villager_door_list()

    spare_cells = list(villager_cells.keys())
    taken = set()          # squares somebody is already standing on
    for index, spec in enumerate(VILLAGERS):
        # WHERE THEY START, AND NOT ON TOP OF EACH OTHER.
        start = None
        if spec.get('at') is not None:
            start = nearest_villager_cell(Vec3(spec['at']))
        if start is None:
            free_doors = [c for c in villager_door_cells if c not in taken]
            if free_doors:
                start = random.choice(free_doors)
        if start is None:
            free = [c for c in spare_cells if c not in taken]
            start = random.choice(free if free else spare_cells)
        taken.add(start)
        # index is what decides their clothes, and it is why villager 3
        # always looks like villager 3 - see the seeding in Villager.__init
        person = Villager(spec, start, index=index)
        at = person.world_position
        print('   villager %d %r at (%.1f, %.1f, %.1f)%s'
              % (index + 1, spec.get('name'), at.x, at.y, at.z,
                 '  [walking]' if person.limbs else '  [stiff - no rig]'))
    hand_out_speeches()
    hand_out_voice_lines()
    place_street_props()
    walking = sum(1 for v in villagers if v.limbs)
    rich = sum(1 for v in villagers if getattr(v, 'is_rich', False))
    print('villagers: %d in the village, %d walking, %d rich'
          % (len(villagers), walking, rich))


def adopt_bench_dialogue():
    try:
        extra = [list(conv) for conv in BENCH_GUY_LINES if conv]
    except Exception:
        return
    if not extra:
        return
    VILLAGE_SPEECHES.extend(extra)
    print('villagers: adopted %d conversations from the men on the benches'
          % len(extra))


def hand_out_textures():
    if not VILLAGER_BODY_TEXTURES:
        return
    deck = list(VILLAGER_BODY_TEXTURES)
    random.shuffle(deck)
    need = [spec for spec in VILLAGERS if not spec.get('rich')]
    for i, spec in enumerate(need):
        if i < len(deck):
            spec['_dealt_texture'] = deck[i]
    if len(need) > len(deck):
        print('!! %d villagers and only %d textures - %d will share. Add '
              'more to VILLAGER_BODY_TEXTURES.'
              % (len(need), len(deck), len(need) - len(deck)))
    else:
        print('villager textures: %d dealt, no two the same' % len(need))


def hand_out_speeches():
    if not VILLAGE_SPEECHES:
        return
    need = [v for v in villagers if not v.talk_lines]
    deck = list(VILLAGE_SPEECHES)
    random.shuffle(deck)
    random.shuffle(need)
    given = 0
    for person, speech in zip(need, deck):
        person.talk_lines = list(speech)
        given += 1
    if given < len(need):
        #ThERES MORE VILLAGERS THAN SPEECHES
        # If I ever want every villager to be unique, the only thing needed
        # is more entries in VILLAGE_SPEECHES
        spare = list(VILLAGE_SPEECHES)
        random.shuffle(spare)
        for i, person in enumerate(need[given:]):
            person.talk_lines = list(spare[i % len(spare)])
        print('   villager speeches: %d of %d villagers share a line, because '
              'there are %d speeches for %d people. Not a fault - add to '
              'VILLAGE_SPEECHES if you want them all unique.'
              % (len(need) - given, len(need),
                 len(VILLAGE_SPEECHES), len(need)))
    print('villager speeches: %d dealt out of %d, each used once'
          % (given, len(VILLAGE_SPEECHES)))


def hand_out_voice_lines():
    if not NPC_ROTATING_VOICES:
        return
    free = [v for v in villagers if not getattr(v, 'talk_voice', None)]
    random.shuffle(free)
    given = 0
    for clip_name, person in zip(NPC_ROTATING_VOICES, free):
        person.talk_voice = clip_name
        given += 1
    if given < len(NPC_ROTATING_VOICES):
        print('!! only %d villagers were free, so %d of my recordings are '
              'not being used this run. Add more villagers to VILLAGERS.'
              % (given, len(NPC_ROTATING_VOICES) - given))
    fixed = [v for v in villagers if getattr(v, 'talk_voice', None)
             and v.talk_voice not in NPC_ROTATING_VOICES]
    print('villager voices: %d recordings dealt out, %d with a scripted '
          'voice of their own, the rest share %r'
          % (given, len(fixed), NPC_VOICE_STAGES[0] if NPC_VOICE_STAGES else None))


build_villagers()

# THE TEXT BOX   (and the spinning head)

#   talk_box      the big one, on the right, always.
#                 the men on the benches, the five house NPCs, and THE
#                 HANDLER down the phone.
#   prompt_box    the small one under it. [E] prompts, and warnings like
#                 "press ESC to close the adverts" or "you weren't supposed
#                 to get here".
#   handler_head  above them both. Only while he is on the phone.
#
# Three layers and some text, drawn in a guaranteed order in the code, specified length.
#
#     1  one of my textbox_bg pictures, STRETCHED to the box. Not tiled - it
#        is a background, so it takes whatever shape the box is.
#     2  a thin dark scrim, TALK_SCRIM, so pale text survives a busy picture.
#        Set it to 0 to see the png completely raw.
#     3  textbox.png, the outline, over the top of both. Its middle has been
#        knocked transparent so the picture shows through the hole.
#     4  the name, then the words, each drawn twice - a pale ghost one pixel
#        off, then the text itself - which is the cheapest way to keep dark
#        text readable over a picture nobody planned for it.
#
# All of it gets forced into panda3d's 'fixed' bin with depth testing off,
# so the adverts still land on top of it, which is correct and funnier.
#
# Every number is here, in one class, so i can move it or restyle it without
# touching anything else. C O N V E N I E N T
_talk_bg_textures = []
_talk_frame_tex = None


def load_talk_skins():
    global _talk_frame_tex
    found = []
    index = build_image_index()
    prefix = TALK_BG_PREFIX.upper()
    for key in sorted(index):
        if key.startswith(prefix):
            tex = crunchy_texture(None, index[key].stem)
            if tex is not None:
                found.append(tex)
    if not found:
        print('!! no %s* images found anywhere in the project - the text '
              'boxes fall back to project textures. Drop your eleven in as '
              '%s_01.png ... %s_11.png and they are picked up automatically.'
              % (TALK_BG_PREFIX, TALK_BG_PREFIX, TALK_BG_PREFIX))
        for name in TALK_BG_FALLBACK:
            tex = crunchy_texture(None, name)
            if tex is not None:
                found.append(tex)
    _talk_frame_tex = crunchy_texture(None, TALK_FRAME_IMAGE)
    if _talk_frame_tex is None:
        print('!! %s.png not found - the boxes will have no outline. It is the '
              'frame you drew; put it anywhere in the project.'
              % TALK_FRAME_IMAGE)
    print('text boxes: %d background pictures, outline %s'
          % (len(found), 'ok' if _talk_frame_tex else 'MISSING'))
    return found


_talk_bg_textures = load_talk_skins()


def paginate(text, width, max_lines):
    # PAGES END WHERE SENTENCES END ROUHGLY, BUT I WAS TOO LAZY TO CONFIGURE IT ALL PERFECTLY ESPECIALLY FOR THE HANDLER.

    # WHAT IT USED TO DO.SOMETHING LIKE THIS so you would read "...and that is the" and
    # have to press E to get "...whole problem."
    #
    # WHAT IT DOES NOW. The paragraph gets split into SENTENCES first, and
    # sentences are then packed into pages one at a time for as long as the
    # page still fits in the box. A page therefore always ends where a sentence ends.
    #
    #
    # The old line-slicing is still here as the fallback, incase i put in a new sentence and something goes wrong idk.
    pages = []
    for chunk in str(text).split('\n\n'):
        chunk = chunk.strip()
        if not chunk:
            continue
        for page in paginate_by_sentence(chunk, width, max_lines):
            if page:
                pages.append(page)
    return pages or ['']


def split_into_sentences(text):
    out = []
    current = ''
    i = 0
    while i < len(text):
        ch = text[i]
        current += ch
        if ch in '.!?':
            # swallow any run of punctuation and  stay together
            while i + 1 < len(text) and text[i + 1] in '.!?':
                i += 1
                current += text[i]
            # a sentence only ends if a space follows, or the text does
            if i + 1 >= len(text) or text[i + 1] in ' \n':
                out.append(current.strip())
                current = ''
        i += 1
    if current.strip():
        out.append(current.strip())
    return out or [text]


def paginate_by_sentence(chunk, width, max_lines):
    pages = []
    sentences = split_into_sentences(chunk)
    page = ''
    for sentence in sentences:
        trial = (page + ' ' + sentence).strip() if page else sentence
        tall = len(wrap_text(trial, width).split('\n'))
        if tall <= max_lines:
            page = trial
            continue
        # it does not fit. Close the page we have and start a new one.
        if page:
            pages.append(page)
            page = ''
        # does this sentence fit on a page of its own?
        tall = len(wrap_text(sentence, width).split('\n'))
        if tall <= max_lines:
            page = sentence
            continue
        # ONE SENTENCE LONGER THAN THE WHOLE BOX, it only cuts after a clause which is very niceee

        for piece in break_at_clauses(sentence, width, max_lines):
            pages.append(piece)
    if page:
        pages.append(page)
    return pages


def break_at_clauses(sentence, width, max_lines):
    # split after each clause mark, keeping the mark on the left-hand piece
    clauses = []
    current = ''
    for ch in sentence:
        current += ch
        if ch in ',;:' or (ch == '-' and len(current) > 12):
            clauses.append(current)
            current = ''
    if current.strip():
        clauses.append(current)

    out = []
    page = ''
    for clause in clauses:
        trial = (page + clause) if page else clause
        if len(wrap_text(trial.strip(), width).split('\n')) <= max_lines:
            page = trial
            continue
        if page:
            out.append(page.strip())
        page = ''
        if len(wrap_text(clause.strip(), width).split('\n')) <= max_lines:
            page = clause
            continue
        # no punctuation to hang it on. Cut by line, as a last resort.
        lines = wrap_text(clause.strip(), width).split('\n')
        for i in range(0, len(lines), max_lines):
            out.append('\n'.join(lines[i:i + max_lines]).strip())
    if page.strip():
        out.append(page.strip())
    return out or [sentence]


def wrap_text(s, width):
    out = []
    for para in str(s).split('\n'):
        out.extend(textwrap.wrap(para, width) or [''])
    return '\n'.join(out)


class SkinnedBox:
    def __init__(self, width, height, y, order, text_scale, wrap,
                 name_scale=TALK_NAME_SCALE, hint=True):
        self.w, self.h, self.y = width, height, y
        self.wrap = wrap
        self.order = order
        self.cx = 0.0
        self.bg = Entity(parent=camera.ui, model='quad', z=-2.20, unlit=True,
                         color=color.white, enabled=False)
        self.scrim = Entity(parent=camera.ui, model='quad', z=-2.21,
                            color=RGB(6, 4, 8, TALK_SCRIM), unlit=True,
                            enabled=False)
        self.frame = Entity(parent=camera.ui, model='quad', z=-2.22,
                            texture=_talk_frame_tex, unlit=True,
                            color=color.white if _talk_frame_tex
                            else RGB(0, 0, 0, 0), enabled=False)
        self.name_text = Text('', parent=camera.ui, origin=(-0.5, 0),
                              z=-2.24, scale=name_scale,
                              color=TALK_NAME_COLOUR, enabled=False)
        self.body_ghost = Text('', parent=camera.ui, origin=(-0.5, 0.5),
                               z=-2.24, scale=text_scale, color=TALK_SHADOW,
                               enabled=False)
        self.body = Text('', parent=camera.ui, origin=(-0.5, 0.5), z=-2.25,
                         scale=text_scale, color=TALK_TEXT_COLOUR,
                         enabled=False)
        self.hint_text = Text('', parent=camera.ui, origin=(0.5, 0), z=-2.25,
                              scale=0.62, color=TALK_NAME_COLOUR,
                              enabled=False) if hint else None
        for n, part in enumerate(self.parts):
            ad_layer(part, order + n)
        for part in (self.body, self.body_ghost):
            try:
                part.line_height = 1.05
            except Exception:
                pass
        self.layout()

    @property
    def parts(self):
        got = [self.bg, self.scrim, self.frame, self.name_text,
               self.body_ghost, self.body]
        if self.hint_text is not None:
            got.append(self.hint_text)
        return got

    def layout(self):
        right = window.aspect_ratio / 2
        cx = right - TALK_BOX_MARGIN - self.w / 2
        self.cx = cx
        for part in (self.bg, self.scrim, self.frame):
            part.position = (cx, self.y)
            part.scale = (self.w, self.h)
        if not TALK_FRAME_OVER:
            # a SOLID outline picture: draw it behind and shrink the
            # background into its hole instead
            self.frame.z = -2.19
            self.bg.scale = (self.w * (1 - 2 * TALK_PAD_X * 0.75),
                             self.h * (1 - 2 * TALK_PAD_Y * 0.75))
            self.scrim.scale = self.bg.scale
        left = cx - self.w / 2 + self.w * TALK_PAD_X
        top = self.y + self.h / 2 - self.h * TALK_PAD_Y
        bottom = self.y - self.h / 2 + self.h * TALK_PAD_Y
        self.name_text.position = (left, top)
        head_room = 0.030 if self.name_text.text else 0.0
        self.body_ghost.position = (left + TALK_SHADOW_OFF,
                                    top - head_room - TALK_SHADOW_OFF)
        self.body.position = (left, top - head_room)
        if self.hint_text is not None:
            self.hint_text.position = (cx + self.w / 2 - self.w * TALK_PAD_X,
                                       bottom)

    def reskin(self):
        if _talk_bg_textures:
            self.bg.texture = random.choice(_talk_bg_textures)
            self.bg.color = color.white
        else:
            self.bg.texture = None
            self.bg.color = RGB(26, 22, 26, 240)

    def set_text(self, words, name='', hint=''):
        self.name_text.text = name
        self.name_text.enabled = bool(name) and self.showing
        for t in (self.body, self.body_ghost):
            t.text = words
        if self.hint_text is not None:
            self.hint_text.text = hint
            self.hint_text.enabled = bool(hint) and self.showing
        self.layout()

    @property
    def showing(self):
        return self.bg.enabled

    def show(self):
        self.reskin()
        self.layout()
        for part in self.parts:
            part.enabled = True
        if not self.name_text.text:
            self.name_text.enabled = False
        if self.hint_text is not None and not self.hint_text.text:
            self.hint_text.enabled = False

    def update(self):
        if not self.showing or len(self.plates) < 2:
            return
        self.plate_timer -= time.dt
        if self.plate_timer > 0:
            return
        self.plate_timer = CEO_PICTURE_SWAP
        self.plate_at = (self.plate_at + 1) % len(self.plates)
        self.picture.texture = self.plates[self.plate_at]

    def hide(self):
        for part in self.parts:
            part.enabled = False


class TalkBox(Entity):
    def __init__(self):
        super().__init__()
        self.box = SkinnedBox(TALK_BOX_WIDTH, TALK_BOX_HEIGHT, TALK_BOX_Y,
                              300, TALK_TEXT_SCALE, TALK_WRAP)
        self.lines = []
        self.at = 0
        self.speaker = None
        self.is_open = False
        self.driven_by_voice = False
        self.full = ''
        self.shown = 0.0
        self.who = ''
        # An optional callback for "this speech has finished". The CEO ending
        # needs it - the button back to the menu is not allowed to appear until
        # you have read the last box - and it is two lines rather than another
        # timer that has to be kept in step with how long the text happens to
        # be.
        self.on_finish = None
        # THE TALKING VOICE
        # The clip that loops while this box is still typing. None means a
        # silent box, which is what the death screen and the notices are.
        # Set by start() and open_for_voice(); cleared by stop_my_voice().
        # See the long note next to HANDLER_VOICE_STAGES in SECTION 3b.
        self.voice_clip = None
        self.voice_volume = 1.0
        # PER LINE (False) or PER TALK (True) - see NPC_VOICE_LOOPS_UNTIL_CLOSE
        self.voice_per_talk = False
        self.voice_started = False
        # False = play once and stop. See VOICE_LOOPS and use_voice().
        self.voice_loops = True

    # the talking voice. Three tiny methods, and nothing else in the game
    # needs to know they exist.
    def start_my_voice(self):
        if self.voice_per_talk and self.voice_started:
            return
        start_voice_clip(self.voice_clip, self.voice_volume, self.voice_loops)
        self.voice_started = True

    def stop_line_voice(self):
        if self.voice_per_talk:
            return
        stop_voice_clip(self.voice_clip)
        self.voice_started = False

    def stop_my_voice(self):
        stop_voice_clip(self.voice_clip)
        self.voice_started = False

    def use_voice(self, clip, volume, per_talk=False, loop=True):
        self.stop_my_voice()
        self.voice_clip = clip
        self.voice_volume = volume
        self.voice_per_talk = bool(per_talk)
        self.voice_loops = bool(loop)
        self.voice_started = False

    # kept so anything that already asks for the talk_box.open still works
    @property
    def open(self):
        return self.is_open

    def start(self, lines, speaker_name='', speaker=None, on_finish=None,
              voice_clip='npc', voice_loop=True):
        if not lines:
            if on_finish:
                on_finish()
            return
        # PICK THE VOICE BEFORE ANYTHING STARTS TYPING.
        # PER TALK for everybody now - the recording runs all the way through
        # and loops until the box closes. The handler used to be the exception;
        # HANDLER_VOICE_PLAYS_THROUGH brought him in line, which is what i
        # meant by no stops between the texts.
        keep_going = NPC_VOICE_LOOPS_UNTIL_CLOSE
        if voice_clip == 'npc':
            self.use_voice(npc_voice_clip(), NPC_VOICE_VOL,
                           per_talk=keep_going, loop=voice_loop)
        elif voice_clip == 'him':
            self.use_voice(handler_voice_clip(), HANDLER_VOICE_VOL,
                           per_talk=HANDLER_VOICE_PLAYS_THROUGH, loop=True)
        elif voice_clip is None:
            self.use_voice(None, 0.0)
        elif isinstance(voice_clip, str):
            # this NPC's own recording. load_voice() always
            # asks for loop=True; use_voice overrides it with voice_loop,
            # which is what makes a monologue play once.
            self.use_voice(load_voice(voice_clip), NPC_VOICE_VOL,
                           per_talk=keep_going, loop=voice_loop)
        else:
            self.use_voice(voice_clip, NPC_VOICE_VOL,
                           per_talk=keep_going, loop=voice_loop)
        self.on_finish = on_finish
        # every line is paged first, so a speech longer than the box
        # becomes several boxes instead of running off the bottom of it
        self.lines = [p for line in lines
                      for p in paginate(line, TALK_WRAP, TALK_MAX_LINES)]
        self.at = -1
        self.speaker = speaker
        self.is_open = True
        self.driven_by_voice = False
        self.box.show()
        show_prompt('')
        if TALK_FREEZE_LOOK:
            player.mouse_sensitivity = Vec2(0, 0)
        self.who = speaker_name
        self.advance()

    def open_for_voice(self, speaker_name='', voice_clip='him',
                       chapter=None, finale=None):
        if voice_clip == 'him':
            # PER TALK + LOOP when HANDLER_VOICE_PLAYS_THROUGH is on, which False puts him back on the old per-line behaviour.
            self.use_voice(handler_voice_clip(chapter, finale),
                           HANDLER_VOICE_VOL,
                           per_talk=HANDLER_VOICE_PLAYS_THROUGH,
                           loop=True)
        elif voice_clip == 'npc':
            self.use_voice(npc_voice_clip(), NPC_VOICE_VOL)
        elif voice_clip is None:
            self.use_voice(None, 0.0)
        else:
            self.use_voice(voice_clip, HANDLER_VOICE_VOL)
        self.lines = []
        self.at = 0
        self.speaker = None
        self.is_open = True
        self.driven_by_voice = True
        self.who = speaker_name
        self.box.show()
        self.set_line('')

    def set_line(self, text, hint=''):
        # already wrapped AND already page-sized by the time it gets here for
        # a conversation; the phone calls come in raw, so wrap them too
        self.full = wrap_text(text, TALK_WRAP)
        self.shown = 0.0 if TALK_TYPEWRITER else len(self.full)
        self.box.set_text(self.full[:int(self.shown)], self.who, hint)
        # THE VOICE STARTS HERE
        # A new line has just gone in the box, so somebody starts talking. If
        # there is no text at all - open_for_voice() opens with an empty box
        # before the first line arrives - stay quiet.
        if self.full:
            self.start_my_voice()
        else:
            self.stop_my_voice()

    def advance(self):
        if self.driven_by_voice:
            return
        if TALK_TYPEWRITER and self.shown < len(self.full):
            self.shown = len(self.full)          # E once = show it all now
            self.box.set_text(self.full, self.who, self.hint_for(self.at))
            # E slammed the whole line onto the screen, so it has "finished
            # typing" and the voice stops with it. Without this, skipping a
            # line would leave him talking over the silence after it.
            # stop_LINE_voice, not stop_my_voice: in PER TALK mode this does
            # nothing and the recording carries on, which is the point.
            self.stop_line_voice()
            return
        self.at += 1
        if self.at >= len(self.lines):
            self.close()
            return
        self.set_line(self.lines[self.at], self.hint_for(self.at))

    def hint_for(self, index):
        return '[E]  end' if index >= len(self.lines) - 1 else '[E]'

    def close(self):
        if not self.is_open:
            return
        #when  the box goes away, whoever was talking stops talking
        self.stop_my_voice()
        # ...and if the camera went round to look at them, it comes back.
        # Safe when it did not: end_dialogue_camera() returns immediately
        # when it is not up, which is every phone call and every ending.
        end_dialogue_camera()
        # every ending has been played out by the chat box - if the chatbox
        # closes the picture should come up every time, to indicate that
        # the player has reached one ending of the game."
        if (game is not None and not self.driven_by_voice
                and game.state in THANKS_CARD_STATES
                and not thanks_card.enabled):
            thanks_card_after()
        self.is_open = False
        self.driven_by_voice = False
        self.lines = []
        # tell the game who has just stopped talking, BEFORE the
        # speaker is forgotten. This is the hook the scientist's lease hangs
        # off - it fires when he has finished, not part way through.
        _who, self.speaker = self.speaker, None
        # whoever asked to be told the speech was over, before the
        # box forgets everything about it
        _done, self.on_finish = self.on_finish, None
        if _done:
            try:
                _done()
            except Exception as exc:
                print('!! a talk-box on_finish callback failed:', exc)
        if _who is not None and game is not None:
            try:
                game.talk_finished(_who)
            except Exception as exc:
                print('!! talk_finished failed:', exc)
        self.full = ''
        self.box.hide()
        if TALK_FREEZE_LOOK:
            player.mouse_sensitivity = MOUSE_SENS

    def notice(self, msg, seconds=None):
        flash_notice(msg, seconds)

    def update(self):
        if not self.is_open or not TALK_TYPEWRITER:
            return
        if self.shown >= len(self.full):
            return
        self.shown = min(len(self.full), self.shown + TALK_TYPE_SPEED * time.dt)
        cut_at = int(self.shown)
        self.box.set_text(self.full[:cut_at], self.who,
                          self.box.hint_text.text if self.box.hint_text else '')
        if cut_at >= len(self.full):
            # PER LINE (the handler): the voice stops here, which is the whole
            # of only playing until the chatbox is read out.
            # PER TALK (everybody else): stop_line_voice() does nothing and the
            # recording keeps running until the box closes.
            self.stop_line_voice()
            if not self.driven_by_voice:
                # a small tick when the line lands, so paging feels like something different

                beep(pitch=-6, length=0.05, wave='square', volume=0.24)


class PromptBox(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)
        y = (TALK_BOX_Y - TALK_BOX_HEIGHT / 2 - PROMPT_BOX_GAP
             - PROMPT_BOX_HEIGHT / 2)
        self.box = SkinnedBox(PROMPT_BOX_WIDTH, PROMPT_BOX_HEIGHT, y, 320,
                              PROMPT_TEXT_SCALE, PROMPT_WRAP, hint=False)
        self.current = ''
        self.notice_text = ''
        self.notice_left = 0.0

    def show(self, msg):
        msg = msg or ''
        if self.notice_left > 0:
            return
        if msg == self.current:
            return
        self.current = msg
        if not msg:
            self.box.hide()
            return
        if not self.box.showing:
            self.box.show()
        self.box.set_text(wrap_text(msg, PROMPT_WRAP), '', '')

    def notice(self, msg, seconds=None, quiet=False):
        self.notice_text = msg
        self.notice_left = NOTICE_SECONDS if seconds is None else seconds
        self.current = None                  # so the prompt redraws afterwards
        if not self.box.showing:
            self.box.show()
        self.box.set_text(wrap_text(msg, PROMPT_WRAP), '', '')
        if not quiet:
            beep(pitch=-10, length=0.06, wave='square', volume=0.18)

    def hide(self):
        self.current = ''
        self.notice_left = 0.0
        self.box.hide()

    def update(self):
        if self.notice_left > 0:
            self.notice_left -= time.dt
            if self.notice_left <= 0:
                self.current = None
                self.box.hide()


# THE HANDLER - telephone man on the phone!

class HandlerHead(Entity):
    def __init__(self):
        super().__init__()
        tex = crunchy_texture(None, HANDLER_HEAD_IMAGE)
        if tex is None:
            print('!! %s.png not found - THE HANDLER has no face. Put it '
                  'anywhere in the project.' % HANDLER_HEAD_IMAGE)
        h = HANDLER_HEAD_HEIGHT
        w = h * ((tex.width / max(1, tex.height)) if tex else 0.62)
        self.head = Entity(parent=camera.ui, model='quad', texture=tex,
                           scale=(w, h), color=color.white if tex
                           else RGB(180, 180, 180),
                           double_sided=True, unlit=True, z=-2.30,
                           enabled=False)
        self.plate = Text(HANDLER_NAME, parent=camera.ui, origin=(0, 0),
                          z=-2.31, scale=0.62, color=RGB(240, 90, 80),
                          enabled=False)
        ad_layer(self.head, 340)
        ad_layer(self.plate, 341)
        self.spin = 0.0
        self.layout()

    def layout(self):
        right = window.aspect_ratio / 2
        cx = right - TALK_BOX_MARGIN - TALK_BOX_WIDTH / 2
        box_top = TALK_BOX_Y + TALK_BOX_HEIGHT / 2
        h = self.head.scale_y
        y = min(0.5 - h / 2 - 0.012, box_top + 0.035 + h / 2)
        self.head.position = (cx, y)
        self.plate.position = (cx, y - h / 2 - 0.022)

    def show(self):
        self.layout()
        self.head.enabled = True
        self.plate.enabled = HANDLER_HEAD_PLATE
        self.spin = 0.0

    def hide(self):
        self.head.enabled = False
        self.plate.enabled = False

    def update(self):
        if not self.head.enabled:
            return
        self.spin += HANDLER_SPIN_SPEED * time.dt
        if HANDLER_SPIN_MODE == 'roll':
            self.head.rotation_z = self.spin % 360
        elif HANDLER_SPIN_MODE == 'sweep':
            self.head.rotation_y = math.sin(math.radians(self.spin)) * HANDLER_SWEEP
        else:                                  # 'spinnnnnnnnnnnnnnnnnnnnnnnnnnn'
            self.head.rotation_y = self.spin % 360


talk_box = TalkBox()
prompt_box = PromptBox()
handler_head = HandlerHead()


# THEIR HEADS DO NOT FOLLOW PLAYER anymore that was weird, i might add that later back though
BENCH_GUY_WATCHES = False


class BenchGuyWatcher(Entity):
    def update(self):
        if not BENCH_GUY_WATCHES:
            return
        if game is None or game.state != 'office' or not city_root.enabled:
            return
        here = player.world_position
        for guy in bench_guys:
            head = getattr(guy, 'head', None)
            if head is None:
                continue
            gap = math.hypot(here.x - guy.x, here.z - guy.z)
            if gap > BENCH_GUY_HEAD_RANGE:
                want = 0.0                 # out of range: face front again
            else:
                # bearing to you in WORLD degrees, minus the way his body faces,
                # leaves the angle his neck actually has to turn
                world = math.degrees(math.atan2(here.x - guy.world_x,
                                                here.z - guy.world_z))
                want = (world - guy.world_rotation_y + 180) % 360 - 180
                want = clamp(want, -BENCH_GUY_HEAD_TURN, BENCH_GUY_HEAD_TURN)
            head.rotation_y = lerp_angle(head.rotation_y, want,
                                         min(1, time.dt * BENCH_GUY_HEAD_SPEED))


bench_guy_watcher = BenchGuyWatcher()


def talkers_here():
    if game is None:
        return ()
    if game.state == 'house':
        return tuple(house_npcs)
    if game.state == 'office':
        # the men on the benches AND the villagers walking about. One list, so E, the dialogue camera and the voice all reach a villager
        # without a single line of villager-specific interaction code!!!!!!!!!! super nice
        return tuple(bench_guys) + tuple(villagers)
    return ()


def talker_in_reach():
    best, best_gap = None, 1e9
    here = player.world_position
    fwd = camera.forward
    for guy in talkers_here():
        if not getattr(guy, 'talk_lines', None):
            continue
        reach = (BENCH_GUY_INTERACT if getattr(guy, 'is_bench_guy', False)
                 else NPC_TALK_RANGE)
        # to the PERSON, via the focus node where there is one - not to the
        # holder's origin, which on the bench model is over a metre off down the bench
        at = getattr(guy, 'focus', guy).world_position
        to = at - here
        gap = math.hypot(to.x, to.z)
        if gap > reach or gap > best_gap:
            continue
        flat = Vec3(to.x, 0, to.z).normalized() if gap > 0.01 else fwd
        if (flat.x * fwd.x + flat.z * fwd.z) < 0.25:   # ~75 degrees either side
            continue
        best, best_gap = guy, gap
    return best


# the old name, kept because it reads better at the call sites in the village, and because im lazy
bench_guy_in_reach = talker_in_reach


INTERACT_FLAGS = ('is_phone', 'is_exit', 'is_house_door', 'is_room_exit',
                  'is_doom_door', 'is_apartment_door', 'is_apartment_entry',
                  'is_throne_exit', 'is_plot_exit', 'talk_lines')


def is_interactive(e):
    return e is not None and any(getattr(e, f, None) for f in INTERACT_FLAGS)


def doors_in_this_scene():
    if game is None:
        return ()
    st = game.state
    out = []
    if st == 'office':
        out += [h.get('door') for h in village_houses]
        out += [apartment_door_outside, door_to_doom]
    elif st == 'house':
        room = (house_rooms[village_houses[game.house_at]['room']]
                if 0 <= game.house_at < len(village_houses)
                and village_houses[game.house_at]['room'] < len(house_rooms)
                else None)
        if room:
            out.append(room.get('exit'))
    elif st == 'apartment':
        out.append(apartment_door_inside)
    elif st == 'throne':
        out.append(throne_exit_door)
    elif st == 'ending':
        out.append(plot_exit_door)
    return tuple(d for d in out if d is not None and d.enabled)


def house_door_in_reach():
    best, best_gap = None, 1e9
    here = player.world_position
    fwd = camera.forward
    for d in doors_in_this_scene():
        to = d.world_position - here
        gap = math.hypot(to.x, to.z)
        if gap > INTERACT_RANGE or gap > best_gap:
            continue
        flat = Vec3(to.x, 0, to.z).normalized() if gap > 0.01 else fwd
        if (flat.x * fwd.x + flat.z * fwd.z) < 0.25:      # ~75 deg either side
            continue
        best, best_gap = d, gap
    return best

# THE MENU - title screen and trophies MENUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU

MENU_WATERMARK_POS  = (-0.558, 0.388)
MENU_WATERMARK_SIZE = (0.378, 0.047)

# screen is loaded in and you can see everything, because right now it
# already starts when the screen is black."
_menu_music = safe_audio(MENU_MUSIC_FILE, loop=True, autoplay=False,
                         volume=MENU_VOLUME)
if _menu_music is None:
    _menu_music = load_sound(MENU_MUSIC_FILE, loop=True, volume=MENU_VOLUME)
if _menu_music is None:
    print('!! %s not found - the title screen will be silent'
          % MENU_MUSIC_FILE)


class MenuMusicStarter(Entity):
    def __init__(self):
        super().__init__()
        self.frames = 0
        self.done = False

    def update(self):
        if self.done or _menu_music is None:
            return
        self.frames += 1
        if self.frames < MENU_MUSIC_WAIT_FRAMES:
            return
        self.done = True
        if _menu_open:
            _menu_music.volume = MENU_VOLUME
            _menu_music.play()
            print('menu music: started after %d drawn frames'
                  % MENU_MUSIC_WAIT_FRAMES)


menu_music_starter = MenuMusicStarter()
doom_music = safe_audio(DOOM_MUSIC, loop=True, autoplay=False,
                        volume=DOOM_MUSIC_VOL)
if doom_music is None:
    print(f'no {DOOM_MUSIC} found - the DOOM levels will be silent')
_menu_bg = Entity(parent=camera.ui, model='quad', texture='menunormal', scale=(1.78, 1.0), z=1)
# nudged right so the whole file fits on screen
_wm = Entity(parent=camera.ui, model='quad',
             texture=crunchy_texture(None, 'watermark'),
             scale=MENU_WATERMARK_SIZE, position=MENU_WATERMARK_POS)

# lifegame.png        PLAY
MENU_BTN_X      = 0.27
MENU_BTN_SIZE   = (0.28, 0.205)         # square-ish,
MENU_BTN_Y      = (0.34, 0.06, -0.25)   # play, control, exit
MENU_MUSIC_POS  = (0.58, -0.29)         # under the bottom button

MENU_TEX_PLAY    = 'lifegame'
MENU_TEX_CONTROL = 'controlredfinal'
MENU_TEX_EXIT    = 'exitbutton'


def _img_button(tex, y, action):
    b = Button(parent=camera.ui, texture=tex, scale=MENU_BTN_SIZE,
               position=(MENU_BTN_X, y),
               color=color.white, highlight_color=RGB(255, 230, 230))
    b.on_click = action
    if b.texture is None:
        print('!! menu button texture %r not found - that button will be a '
              'blank white bar until the png is in the project' % tex)
    return b


def _menu_play():
    _set_menu(False)
    game.begin()


# Press the control button and controlredneckman fills the
# middle of the screen for two seconds. / side effects it  will lowk put you back to the start of the game always
CONTROL_FLASH_IMAGE = 'controlredneckmanNEW'
CONTROL_FLASH_ASPECT = 873 / 1052      # measured off the file
CONTROL_FLASH_HEIGHT = 0.43            # was 0.86 - exactly 2x smaller
control_flash = Entity(parent=camera.ui, model='quad',
                       texture=safe_texture(CONTROL_FLASH_IMAGE),
                       scale=(CONTROL_FLASH_HEIGHT * CONTROL_FLASH_ASPECT,
                              CONTROL_FLASH_HEIGHT),
                       z=-3, enabled=False)
if control_flash.texture is None:
    print(f'!! {CONTROL_FLASH_IMAGE}.png not found - the controls flash will '
          f'be an empty square until it is somewhere in the project')


def show_control_flash():
    control_flash.enabled = True
    invoke(setattr, control_flash, 'enabled', False, delay=2.0)


# THE ADS / LOOKING BAKC THIS FEATURE IS JUST ANNOYING BUT IT FITS THE UNIVERSE AND STORY
#This is my meta-glasses idea

ADS_ON          = True
AD_EVERY        = (10.0, 35.0)     # was (28, 70) - twice as often
AD_MAX_ON_SCREEN = 20               # was 3. Smaller ads, so more of them fit
AD_WIDTH        = (0.17, 0.26)     # was (0.34, 0.52) - half the size
AD_CLICK_ANYWHERE = False          # True = a click anywhere closes the top ad
AD_IN_MENU      = True             # they turn up on the main menu too
AD_MENU_EVERY   = (9.0, 22.0)      # the menu gets them faster, you can click
AD_HINT_SECONDS = 2.6              # how long "[ESC] to close" shows for
# sound when they appear, it is annoying, I might add something there lateeeeer

AD_SOUNDS_ON    = False
# More spots, because there are more and smaller adverts now and two landing
# on the same pixel looks like a mistake rather than a mess.
AD_SPOTS        = [(-0.60, 0.30), (-0.30, 0.34), (0.02, 0.32), (0.34, 0.34),
                   (0.62, 0.30), (-0.62, 0.02), (0.64, 0.04), (-0.58, -0.26),
                   (-0.26, -0.30), (0.06, -0.32), (0.36, -0.28), (0.62, -0.24),
                   (-0.34, 0.10), (0.30, -0.06)]

AD_FEATURED = ['monthlysubscription', 'greenieface', 'perfectbody',
               'lifecourse',
               'house100',
               'Jasper imageORDER',
               'SUITNEW',
               'cover_edit_heavy',
               'watchtimeMEME',
               'progresstexture',
               'laterent',
               'humanSUpremacy']
AD_FAVOURITE_WEIGHT = 10            # was 4 so i remember

# WEIRDER PICTURES
AD_FILLER = [
    # faces looking back at you
    'greeter_face', 'grandma', 'grandma2', 'grandma3', 'menuhuman',
    'menunaked', 'menugreen',
    'eye 1', 'eye 2',
    'ribcage', 'guts', 'nerves', 'red neck together', 'red_marble',
    'Enemy_MegafuckElite2', 'Enemy_Security2', 'Enemy_Orange', 'doom_gun',
    'funko', 'easteregg_photo', 'oven',
    'walled_window', 'controlredfinal', 'fulltemplate model',
]

AD_IMAGES = (AD_FEATURED * AD_FAVOURITE_WEIGHT
             + [n for n in AD_FILLER if n not in AD_FEATURED])

# the adverts were costing frames, and it was not the drawing it was the LOADING - every advert image was going onto the graphics card at full size
AD_THUMB_SUFFIX = '_ad'


def ad_texture(name):
    return crunchy_texture(None, name + AD_THUMB_SUFFIX) or crunchy_texture(None, name)


_ad_textures = []
_ad_missing = []
_ad_fullsize = []
AD_THUMB_MAX = 256      # anything already this small needs no thumbnail
for _n in dict.fromkeys(AD_IMAGES):
    _t0 = ad_texture(_n)
    if _t0 is None:
        _ad_missing.append(_n)
    elif crunchy_texture(None, _n + AD_THUMB_SUFFIX) is None:
        # only worth mentioning if the full-size image is actually BIG
        # most of the meat and face textures are already 256x256 and a
        # thumbnail of them would be pointless
        try:
            if max(_t0.width, _t0.height) > AD_THUMB_MAX:
                _ad_fullsize.append(_n)
        except Exception:
            pass
for _n in AD_IMAGES:                       # weighted, so keep the duplicates
    _t = ad_texture(_n)
    if _t is not None:
        _ad_textures.append(_t)
if _ad_fullsize:
    print('   ads: no %s.png thumbnail for %s - using the full-size image, '
          'which costs video memory. Run tools_shrink_ads.py.'
          % (AD_THUMB_SUFFIX, ', '.join(_ad_fullsize[:6])
             + (' ...' if len(_ad_fullsize) > 6 else '')))
_ad_yours = sum(1 for _n in AD_IMAGES
                if _n in AD_FEATURED and _n not in _ad_missing)
print('ads: %d images loaded, %d in the draw pile - %d of those (%.0f%%) are '
      'YOURS (%d pictures x%d)'
      % (len(dict.fromkeys(AD_IMAGES)) - len(_ad_missing), len(_ad_textures),
         _ad_yours, 100.0 * _ad_yours / max(1, len(_ad_textures)),
         len([n for n in AD_FEATURED if n not in _ad_missing]),
         AD_FAVOURITE_WEIGHT))
if _ad_missing:
    yours = [n for n in _ad_missing if n in AD_FEATURED]
    if yours:
        print('   !! ONE OF YOUR OWN ADS IS MISSING: %s  -> put %s.png '
              'anywhere in the project' % (', '.join(yours), yours[0]))
    print('   !! ad images NOT FOUND, they are simply skipped: %s'
          % ', '.join(_ad_missing))

# One image, covering the whole screen, when the boss dies and the baaaad ending starts.
# it sits in front of everything except the fade.

ENDING_CARD_TEXTURE = 'bossending'      # 1920x1080.jpg
ENDING_CARD_SECONDS = 6.0               # how long it holds before fading out
ENDING_CARD_FADE    = 1.2

# full detail - it fills the screen, see the note on FULL_DETAIL ^^^ somwheee up theeeeere
_ending_card_tex = crunchy_texture(None, ENDING_CARD_TEXTURE, detail=FULL_DETAIL)
if _ending_card_tex is None:
    print('!! %s not found - the kill ending will play without its '
          'card.' % ENDING_CARD_TEXTURE)
ending_card = Entity(parent=camera.ui, model='quad',
                     texture=_ending_card_tex,
                     scale=(2.0, 1.2), z=-2.4, enabled=False)
make_fog_proof(ending_card)


def show_ending_card(seconds=None):
    if ending_card.texture is None:
        return
    seconds = ENDING_CARD_SECONDS if seconds is None else seconds
    ending_card.enabled = True
    ending_card.alpha = 1
    ending_card.animate('alpha', 0, duration=ENDING_CARD_FADE,
                        delay=max(0.0, seconds - ENDING_CARD_FADE))
    invoke(setattr, ending_card, 'enabled', False, delay=seconds + 0.1)

THANKS_CARD_TEXTURE = 'bathroom_bloodTHANKS'
THANKS_CARD_DELAY   = 1.0      # seconds after the last line is read
THANKS_CARD_HEIGHT  = 0.62
THANKS_CARD_AT      = (0, 0.06)
THANKS_CARD_FADE    = 0.8
# How long it holds on screen before the game ends.
THANKS_CARD_HOLD    = 8.0
THANKS_CARD_STATES = ('ending', 'transition', 'throne')
THANKS_CARD_OUT     = 1.6      # the fade to black after it

# TEXTURE_DETAIL is 'low' for the whole game, and a quarter-size copy of something this big on
# screen would be mush. See the note on FULL_DETAIL.
_thanks_tex = crunchy_texture(None, THANKS_CARD_TEXTURE, detail=FULL_DETAIL)
if _thanks_tex is None:
    print('!! %s.png not found - the endings will finish without the thanks '
          'card. Drop the file anywhere in the project.' % THANKS_CARD_TEXTURE)
    _thanks_aspect = 1.0
else:
    # real proportions, off the file itself, so it is never stretched
    _thanks_aspect = ((_thanks_tex.width / _thanks_tex.height)
                      if getattr(_thanks_tex, 'height', 0) else 1.0)

thanks_card = Entity(parent=camera.ui, model='quad',
                     texture=_thanks_tex,
                     scale=(THANKS_CARD_HEIGHT * _thanks_aspect,
                            THANKS_CARD_HEIGHT),
                     position=THANKS_CARD_AT,
                     z=-2.6,              # in front of the ending card
                     enabled=False)
make_fog_proof(thanks_card)
# same order so nothing can end up painted over the top of it.
ad_layer(thanks_card, AD_BIN_ORDER + 40)

def show_thanks_card():
    if thanks_card.texture is None:
        return
    if thanks_card.enabled:
        return                      # already up - do not restart the fade
    thanks_card.enabled = True
    thanks_card.alpha = 0
    thanks_card.animate('alpha', 1, duration=THANKS_CARD_FADE)
    print('   THANKS: that was the game.')
    invoke(finish_after_thanks, delay=THANKS_CARD_FADE + THANKS_CARD_HOLD)


def finish_after_thanks():
    if not thanks_card.enabled:
        return                      # already cleared by hand
    hide_thanks_card()
    if game is None:
        return
    if game.state == 'menu':
        return
    game.credits_after_thanks = False
    fade_to_black(THANKS_CARD_OUT, then=game._back_to_menu)


def hide_thanks_card():
    if not thanks_card.enabled:
        return
    thanks_card.animate('alpha', 0, duration=0.35)
    invoke(setattr, thanks_card, 'enabled', False, delay=0.4)
    if game is not None and getattr(game, 'credits_after_thanks', False):
        game.credits_after_thanks = False
        invoke(game.roll_credits, delay=0.45)


def thanks_card_after(then=None, delay=None):
    delay = THANKS_CARD_DELAY if delay is None else delay

    def go():
        # ONE TROPHY PER ENDING, AWARDED HERE SHOULD BE DIFFERNET FOR EACH EPRSO NWHO INSTALLS THE FOLDERS AND FILES

        # thanks_card_after() gets called by every ending there is, so this is the one place that sees all of them
        if game is not None:
            unlock_trophy(trophy_for_this_ending(game))
        show_thanks_card()
        if then:
            try:
                then()
            except Exception as exc:
                print('!! the callback after the thanks card failed:', exc)

    invoke(go, delay=delay)


#my mp4 of th entropy sign!!!, playing forever in the corner of the screen while you can move.
# HOW IT IS DONE, and why not a video:
ENTROPY_ON       = True
ENTROPY_FOLDER   = 'entropy'
ENTROPY_FPS      = 30
ENTROPY_SIZE     = 0.50         #
ENTROPY_POS      = (-0.74 + ENTROPY_SIZE, 0.40 - ENTROPY_SIZE / 2)
ENTROPY_CHROMA_KEY = True
ENTROPY_KEY_CUTOFF = 0.34
ENTROPY_KEY_SOFT   = 0.22
ENTROPY_ADDITIVE   = True
ENTROPY_ALPHA    = 0.85
ENTROPY_SHOW_STATES = {'office', 'apartment', 'house', 'doom', 'finale',
                       'ending', 'djhouse'}


def load_entropy_frames():
    folder = None
    names = ([ENTROPY_FOLDER + '_keyed', ENTROPY_FOLDER] if ENTROPY_CHROMA_KEY
             else [ENTROPY_FOLDER])
    for want in names:
        # not a fresh walk - see find_folder()
        cand = find_folder(want)
        if cand is not None and cand.is_dir() and any(
                f.suffix.lower() in IMAGE_TYPES for f in cand.iterdir()):
            folder = cand
            break
        if folder is not None:
            break
    if folder is None:
        print('!! no %s/ folder - the ENTROPY loop will not appear. '
              'Run the ffmpeg line in the note above to make it.'
              % ENTROPY_FOLDER)
        return []
    files = sorted(f for f in folder.iterdir()
                   if f.suffix.lower() in IMAGE_TYPES)
    out = []
    for f in files:
        try:
            t = Texture(str(f))
            t.filtering = None          # keep it blocky
            out.append(t)
        except Exception as e:
            print('!! %s failed to load: %s' % (f.name, e))
    print('entropy: %d frames loaded from %s/ (%.1fs loop at %d fps)'
          % (len(out), folder.name, len(out) / max(1, ENTROPY_FPS), ENTROPY_FPS))
    return out


_entropy_frames = load_entropy_frames() if ENTROPY_ON else []

entropy_widget = Entity(parent=camera.ui, model='quad',
                        texture=_entropy_frames[0] if _entropy_frames else None,
                        scale=(ENTROPY_SIZE, ENTROPY_SIZE),
                        position=ENTROPY_POS, z=-1.2,
                        color=RGB(255, 255, 255, int(ENTROPY_ALPHA * 255)),
                        enabled=False)
make_fog_proof(entropy_widget)
# additive blending, so black contributes nothing and the letters glow over whatever is behind them
if ENTROPY_ADDITIVE:
    try:
        entropy_widget.blend_mode = 'add'
    except Exception:
        try:
            from panda3d.core import ColorBlendAttrib
            entropy_widget.setAttrib(ColorBlendAttrib.make(
                ColorBlendAttrib.M_add,
                ColorBlendAttrib.O_incoming_alpha,
                ColorBlendAttrib.O_one))
        except Exception as e:
            print('   (entropy: additive blending unavailable, %s)' % e)


class EntropyLoop(Entity):
    def __init__(self):
        super().__init__()
        self.t = 0.0
        self.i = 0

    def update(self):
        if not _entropy_frames:
            return
        # only while you are actually playing
        show = (not _menu_open and not application.paused and not _paused_menu
                and game is not None
                and game.state in ENTROPY_SHOW_STATES
                and player.enabled)
        if entropy_widget.enabled != show:
            entropy_widget.enabled = show
        if not show:
            return
        self.t += time.dt
        step = 1.0 / max(1, ENTROPY_FPS)
        while self.t >= step:
            self.t -= step
            self.i = (self.i + 1) % len(_entropy_frames)
            entropy_widget.texture = _entropy_frames[self.i]


entropy_loop = EntropyLoop()


open_ads = []          # every advert currently in your face
#I messed up the  draw order which is why it wasnt workign for a while.
class Advert(Entity):
    def __init__(self, tex):
        w = random.uniform(*AD_WIDTH)
        h = w * random.uniform(0.62, 1.05)         # never a perfect square
        x, y = random.choice(AD_SPOTS)
        # nudge, so two adverts sharing a spot are not exactly on top of
        # each other and you can still see there are two X's to click
        x += random.uniform(-0.035, 0.035)
        y += random.uniform(-0.035, 0.035)

        super().__init__(parent=camera.ui, model='quad', texture=tex,
                         scale=(w, h), position=(x, y), z=-3.4,
                         color=color.white, unlit=True)
        ad_layer(self, AD_BIN_ORDER)
        #keeps it SQUARE on screen whatever shape the advert
        box = 0.26
        self.close = Button(parent=self, model='quad',
                            scale=(box, box * (w / h)),
                            position=(0.5 - box * 0.62,
                                      0.5 - box * (w / h) * 0.62),
                            z=-0.06,
                            color=RGB(205, 25, 25),
                            highlight_color=RGB(255, 90, 90))
        ad_layer(self.close, AD_BIN_ORDER + 1)

        for _rot in (45, -45):
            ad_layer(Entity(parent=self.close, model='quad', rotation_z=_rot,
                            z=-0.02, scale=(0.74, 0.19),
                            color=RGB(255, 255, 255), unlit=True),
                     AD_BIN_ORDER + 2)
        self.close.on_click = self.dismiss
        # WHERE THE X IS ON SCREEN, worked it out once and used it every time
        self.close_centre = Vec2(x + self.close.x * w, y + self.close.y * h)
        self.close_half = box * w * 0.5 * 1.35     # 35% grace

        open_ads.append(self)
        # It just appears, which is more like a real pop-up
        # anyway.
        show_ad_hint()

    def hit_close(self, mx, my):
        return (abs(mx - self.close_centre.x) < self.close_half
                and abs(my - self.close_centre.y) < self.close_half)

    def dismiss(self):
        if self in open_ads:
            open_ads.remove(self)
        destroy(self)


class AdClicker(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)

    def input(self, key):
        if key != 'left mouse down' or not open_ads or not ADS_ON:
            return
        if getattr(mouse, 'locked', False):
            #  cursor is locekd
            show_ad_hint()
            return
        mx, my = mouse.x, mouse.y
        # newest first, so the one on top is the one you close
        for ad in reversed(list(open_ads)):
            if ad.hit_close(mx, my):
                ad.dismiss()

# AD_SOUNDS_ON back to True, or replace the beep with load_sound('yourfile').play().
                if AD_SOUNDS_ON:
                    beep(pitch=8, length=0.06, wave='square', volume=0.25)
                return
        if AD_CLICK_ANYWHERE:
            close_top_ad()


ad_clicker = AdClicker()


# THE HINT, A single line telling you what to do about the ads in the text pop
ad_hint = Text('[ESC]  then click the red X', parent=camera.ui, origin=(0, 0),
               position=(0, -0.46), scale=0.75, color=RGB(255, 90, 90),
               z=-3.5, enabled=False)
ad_hint.setFogOff(1)
_ad_hint_until = 0.0


def show_ad_hint():
    global _ad_hint_until
    msg = ('press esc to pause and skip the ads, or just take off your meta '
           'glasses weirdo.' if getattr(mouse, 'locked', False)
           else 'click the red X to close the advert')
    # "press esc to cancel ads" is one of the notices, so it goes in the text box with everything else rather than being its own floating red line.
    # The old line is still there and still works - set PROMPTS_IN_BOX False and it comes back.
    if PROMPTS_IN_BOX and prompt_box is not None:
        # AD_SOUNDS_ON - this is the tick you get when an advert ARRIVES, because an arriving advert puts this hint in the box and the box ticks.
        # It was annoying, so it is off, i didnt like it.
        flash_notice(msg, AD_HINT_SECONDS, quiet=not AD_SOUNDS_ON)
        return
    ad_hint.text = msg
    _ad_hint_until = time.time() + AD_HINT_SECONDS
    ad_hint.enabled = True


def close_top_ad():
    if open_ads:
        open_ads[-1].dismiss()
        return True
    return False


def clear_all_ads():
    for a in list(open_ads):
        a.dismiss()


class AdBroker(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)
        # The game opens on the title screen, so the FIRST advert is a menu
        # advert and gets the menu's shorter timer. Starting it on AD_EVERY
        # meant i could sit on the menu for over half a minute before one urned up.
        self.t = random.uniform(*AD_MENU_EVERY)

    def update(self):
        # the hint fades itself out whether or not anything else is running
        if ad_hint.enabled and (time.time() > _ad_hint_until or not open_ads):
            ad_hint.enabled = False

        if not ADS_ON or not _ad_textures:
            return

        # ON THE TITLE SCREEN STARTING MENU
        if _menu_open:
            if not AD_IN_MENU:
                return
            self.t -= time.dt
            if self.t > 0:
                return
            self.t = random.uniform(*AD_MENU_EVERY)
            if len(open_ads) < AD_MAX_ON_SCREEN:
                Advert(random.choice(_ad_textures))
            return

        # IN GAME ADVERTS
        # No new ones while you are paused and clearing them. time.dt still
        # ticks because this entity ignores the pause, so the timer gets frozen
        # by hand here instead, also during the hold on time in doom level when they are trying to kill you.
        if application.paused or _paused_menu:
            return
        # and none over an ending. The CEO screen is deliberately drawn
        # UNDER the text box so the speech reads over the picture - will land on top of everything.
        if game is None or game.state in ('menu', 'transition', 'ending'):
            return
        self.t -= time.dt
        if self.t > 0:
            return
        self.t = random.uniform(*AD_EVERY)
        if len(open_ads) >= AD_MAX_ON_SCREEN:
            return
        Advert(random.choice(_ad_textures))


ad_broker = AdBroker()

# THE THREE ENDINGS, AND WHICH TROPHY EACH ONE GIVES !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
TROPHIES_ON   = True
SAVE_FILE     = 'save_state.json' # seperate for each person who plays the game
TROPHY_ORDER  = ['demonENDING', 'killingEnding', 'happyENDING']
TROPHY_LABELS = {
    'demonENDING':   'PSYCHOPATH',
    'killingEnding': 'THE CEO OF YOURSELF',
    'happyENDING':   'you are the eternal malice',
}
TROPHY_HEIGHT = 0.30
TROPHY_GAP    = 0.15
TROPHY_Y      = 0.02
TROPHY_NONE_TEXT = 'No endings unlocked'
# the back button on the cabinet.
TROPHY_BACK_IMAGE = 'controlredfinal'
TROPHY_BACK_SIZE  = (0.22, 0.17)
TROPHY_BACK_Y     = -0.20
#Shift+J wipes them again. and pressign it get you the trophies  - i was lazy and didnt remove this so maybe noone will know : )
TROPHY_TEST_KEY = 'j'

# THE SAVE BELONGS TO THE PLAYER, NOT TO THE GAME
SAVE_DIR_NAME = '.eternalmalice'

def save_path():
    try:
        from pathlib import Path as _SavePath
        folder = _SavePath.home() / SAVE_DIR_NAME
        folder.mkdir(parents=True, exist_ok=True)
        return folder / SAVE_FILE
    except Exception:
        return ASSETS / SAVE_FILE


def load_save():
    if not TROPHIES_ON:
        return {'trophies': []}
    try:
        path = save_path()
        if not path.exists():
            return {'trophies': []}
        with open(path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {'trophies': []}
        data.setdefault('trophies', [])
        return data
    except Exception as exc:
        print('!! could not read %s (%s) - starting with no trophies'
              % (SAVE_FILE, exc))
        return {'trophies': []}


def write_save():
    if not TROPHIES_ON:
        return
    try:
        with open(save_path(), 'w') as f:
            json.dump(SAVE, f, indent=2)
    except Exception as exc:
        print('!! could not write %s (%s) - this run will not be remembered'
              % (SAVE_FILE, exc))


SAVE = load_save()


def unlock_trophy(name):
    if not TROPHIES_ON or name not in TROPHY_ORDER:
        return
    if name in SAVE['trophies']:
        return
    SAVE['trophies'].append(name)
    write_save()
    print('   TROPHY: %s unlocked (%d of %d)'
          % (name, len(SAVE['trophies']), len(TROPHY_ORDER)))
    flash_notice('ending unlocked - see CONTROL on the menu', 6.0)


def trophy_for_this_ending(game_state):
    if getattr(game_state, 'boss_killed', False):
        return 'demonENDING'
    if getattr(game_state, 'livers', 0) > 0:
        return 'killingEnding'
    return 'happyENDING'


def _menu_options():
    show_control_flash()
    trophy_screen.toggle()


def _menu_quit():
    application.quit()


def _toggle_music():
    global _music_muted
    _music_muted = not _music_muted
    if _menu_music:
        _menu_music.volume = 0.0 if _music_muted else 0.7
    _btn_mute.texture = _MUSIC_TEX_OFF if _music_muted else _MUSIC_TEX_ON


_music_muted = False
_MUSIC_TEX_ON = safe_texture('musicon')
_MUSIC_TEX_OFF = safe_texture('musicoff')
if _MUSIC_TEX_ON is None or _MUSIC_TEX_OFF is None:
    print('!! musicon.png / musicoff.png not found - the music button will be '
          'a blank square until they are somewhere in the project')
# just a basic square to turn musci off incase anyone wants to sit on main menu and read
MUSIC_BUTTON_SIZE = 0.11 * 1.5

# MENU_MUSIC_POS is up with the other menu layout numbers.
_btn_mute = Button(parent=camera.ui, texture=_MUSIC_TEX_ON,
                   scale=(MUSIC_BUTTON_SIZE, MUSIC_BUTTON_SIZE),
                   position=MENU_MUSIC_POS, color=color.white,
                   highlight_color=RGB(255, 235, 235))
_btn_mute.on_click = _toggle_music

# all five are on the title screen at once, scattered around the picture: each one gets a rainbow coloured font.
MENU_PARAGRAPHS = [
    # 1
    "Don't be fooled, it is not over yet you have simply reached the best "
    "part, by choosing to not follow down a path of golden age you have truly "
    "eradicated all sense of laziness. Now, you will not get sucked into a "
    "single existence, time travel is not real, but rebirth is always an "
    "option, with the cost of life being so incredibly low there is truly a "
    "point in wasting your life now. Go out and find your way in this "
    "automatoid flesh, you have persevered, This is my way of saying goodbye\n"
    "'Cause I can't do it face to face, I'm talking to you before, at the "
    "pearly gates, this is one for the good days no matter what happens now "
    "you shouldn't be afraid. live your life in a recently signed and sealed "
    "contract, bought, real, signed, no mortgage, rent free, 25 square "
    "meters, house, in a resident area, free of landlords and monthly "
    "check-ups, no electricity bill, alone, weekly garbage trucks, and truly "
    "an eternal malice.",
    # 2
    "Although you will be forever trapped in your boundless blues, as the ceo "
    "of yourself you will forever lack knowledge and understanding, the past "
    "is ever present, you will be trapped forever, the sun smiles at you and "
    "you are overwhelmed with rotten husk, boundless power. You may have the "
    "soul of an emperor, but you weep and stink of the worst thing that you "
    "always swore you would not become.\n\n"
    "Set goals, have a resolution, have a ten year plan, work quarterly, "
    "invest, wake up early, have a boundless optimal mindset. Good luck",
    # 3
    "In the deepest ocean, your eyes, they turn me, they tell me, they say to "
    "me.\nWhy should I stay here, after all, why should I stay.\n"
    "I would be crazy not to follow, follow where you lead, your eyes, they "
    "tell me\nTurn me on to phantoms, I follow to the edge of the earth, and "
    "fall off.\n\nYou are not to blame for, Bittersweet distractors, Dare not "
    "speak its name\nDedicated to all human beings, because we separate like "
    "ripples on a blank shore\n\nEverybody would, Everybody leaves, if they "
    "get the chance, a way out and this, this is my chance, i get eaten by "
    "the worms, and weird fishes, picked over by the worms and weird fishes, "
    "i hit the bottom, i hit rock bottom and escape.\nBlown out speakers, "
    "Fireworks and hurricanes, rainbows and butterflies I'm not here, This "
    "isn't happening, I never really got there, I just pretended that I had, "
    "You've got a light, you can feel it on your back A light, you can feel "
    "it on your back",
    # 4
    '"The living organism, in a situation determined by the play of energy '
    "on the surface of the globe, ordinarily receives more energy than is "
    "necessary for maintaining life, It has come to my attention that, "
    "without profit, it must be spent, willingly or not, gloriously or "
    "catasthropically. The layers have been peeled off one by one, it comes "
    "to us all, How come I end up where ive started with you, how come i end "
    "up where i went wrong, you become a condensed balance of operations a "
    "rotation of 38 degrees.  You killed the sound\nRemoved backbone A pale "
    "imitation With the edges sawn off. Blink your eyes\nOne for yes\n"
    "Two for no They got a skin and they put you in\nOh, the lines wrapped "
    "'round your face  are now for everyone else to see. YOU ARE TRUELY "
    "ALIVE. The ultimate trauma loop of, the one who seeked to destroy the "
    "matter of which themselves is brought up on, there is nothing left for "
    "you other than a pity of trauma in endless grace of power",
    # 5
    "Perhaps more effective than all other forms, the digital spaces of "
    "video games represent the production of desire at its most "
    "totalitarian, with a history of game design and commodification built "
    "directly from the behaviorist research of B.F. Skinner (Yee, 2006).  "
    "This society is frozen, perpetuated, like a chrysalis of a corpse "
    "butterfly, suggesting the possibility of growth, but in fact not "
    "allowing any sign of grow/advancement past the preconceived limits set "
    "by the game itself",
]
# NOTE: paragraphs 1-5 above are kept exactly the same from the source material of how I wrote them.
#HERE the snippts are a bit sliced up to add the feel to the menu or randomness and random lines.

MENU_ENDING_SNIPPETS = {

    'demonENDING': [
        "The transfer clears, four hundred a life... Grey Matter Technologies "
        "thanks you for your co-work and participation in the survey.\n\n"
        "There is a house at the end of the road with FOR SALE painted on the "
        "door.",

        "Although you will be forever trapped in your boundless blues, as the "
        "CEO of yourself, you will forever lack knowledge and understanding, "
        "the past is ever present, you will be trapped forever.",
    ],

    'killingEnding': [
        "You may have the soul of an emperor... but you weep and stink of the "
        "worst thing that you always swore you would not become.",

        "Go out and find your way in this AUTOMATOID FLESH, you have "
        "persevered. Live your life in a recently signed and sealed contract, "
        "bought, real, signed, no mortgage, rent free, 25 square meters, "
        "alone, weekly garbage trucks, TRULY AN ETERNAL MALICE.",
    ],

    'happyENDING': [
        "Somebody in this village has been waiting years for a true Divine "
        "malice, a Divine Light that has not yet been shattered by the disgust "
        "of this world...",

        "Do you understand what that is? That is not restraint. Restraint is a "
        "structure, you have preserved your humanity, and therefore you have "
        "entangled your divine light!",

        "In the deepest ocean, your eyes, they turn me, they tell me, they say "
        "to me. Why should I stay here, after all, why should I stay.",
    ],
}
#The rest of the space goes to MENU_PARAGRAPHS.
MENU_ENDING_SLOTS = 4


def menu_text_pool():
    try:
        got = set(SAVE.get('trophies', []))
    except Exception:
        got = set()
    locked, seen = [], []
    for trophy in TROPHY_ORDER:
        bucket = locked if trophy not in got else seen
        bucket.extend(MENU_ENDING_SNIPPETS.get(trophy, []))
    random.shuffle(locked)
    random.shuffle(seen)
    # locked first: an ending you have not reached gets the screen space
    picked = (locked + seen)[:MENU_ENDING_SLOTS]
    rest = MENU_PARAGRAPHS[:]
    random.shuffle(rest)
    out = picked + rest
    return out[:len(MENU_PARA_ZONES)]

# ROYGBIV, one per paragraph (5 paragraphs = 5 stops of the rainbow).
# A full rainbow now rather than five stops, so nine paragraphs still all get
# their own colour instead of two of them coming out the same red.
MENU_RAINBOW = [
    RGB(255, 70, 70),      # red
    RGB(255, 160, 40),     # orange
    RGB(250, 235, 60),     # yellow
    RGB(90, 235, 90),      # green
    RGB(60, 225, 210),     # cyan
    RGB(120, 150, 255),    # blue
    RGB(190, 110, 255),    # violet
    RGB(255, 90, 200),     # magenta
    RGB(255, 255, 255),    # white
]
# Sizes: "barely readable like they are right now but not bigger than that".
MENU_PARA_SCALE = (0.26, 0.40)
# Loose zones around the picture (top-left corners), jittered each time the
# menu opens so the placement is random but the blocks stay on screen and
# always dead horizontal. There are more of them than there used to be because
# there are more paragraphs; the right-hand column stops short of the buttons
# so nothing lands on top of PLAY.
MENU_PARA_ZONES = [(-0.87, 0.475), (-0.87, 0.10), (-0.87, -0.22),
                   (-0.50, 0.475), (-0.50, 0.06), (-0.50, -0.26),
                   (-0.13, 0.475), (-0.13, -0.02), (-0.13, -0.30),
                   (0.20, -0.10), (0.20, -0.34)]


def _build_menu_paragraphs():
    out = []
    for i in range(len(MENU_PARA_ZONES)):
        # WHY THE TEXT IS NOT EMPTY, AND WHY wordwrap IS SET AFTER
        # Two traps in ursina's Text, both of which I walked into:
        #
        # 1. Text.__init__ ends with `if text != '': self.text = text`. Pass
        #    an empty string and it SKIPS the assignment entirely, so
        #    self.raw_text is never created.
        # 2. the `wordwrap` setter's first line is
        #    `for line in self.raw_text.split('\n')`.
        #
        # So `Text('', wordwrap=50)` raises AttributeError: 'Text' object has
        # no attribute 'raw_text' - the kwarg loop reaches wordwrap before
        # anything has ever set the text. That is the crash.
        #
        # A single space is enough to make ursina take the assignment and
        # create raw_text, and wordwrap is applied afterwards, by which
        # point it has something to read. The scatter overwrites both a
        # moment later anyway.
        t = Text(' ', parent=camera.ui, origin=(-0.5, 0.5),
                 scale=random.uniform(*MENU_PARA_SCALE),
                 color=MENU_RAINBOW[i % len(MENU_RAINBOW)],
                 line_height=0.95)
        t.wordwrap = random.randint(40, 60)
        try:
            t.font = 'comic.ttf'       # real Comic Sans if it's in the project
        except Exception:
            pass
        t.rotation_z = 0               # horizontal, always - no angles
        out.append(t)
    return out


def _scatter_menu_paragraphs():
    pool = menu_text_pool()
    zones = MENU_PARA_ZONES[:]
    random.shuffle(zones)
    for i, t in enumerate(_menu_paras):
        if i >= len(pool):
            t.enabled = False
            continue
        t.enabled = True
        t.text = pool[i]
        zx, zy = zones[i % len(zones)]
        t.position = (zx + random.uniform(-0.05, 0.05),
                      zy + random.uniform(-0.03, 0.03))
        t.scale = random.uniform(*MENU_PARA_SCALE)
        t.color = MENU_RAINBOW[i % len(MENU_RAINBOW)]
        t.wordwrap = random.randint(40, 60)


_menu_paras = _build_menu_paragraphs()
_scatter_menu_paragraphs()

_btn_play = _img_button(MENU_TEX_PLAY,    MENU_BTN_Y[0], _menu_play)
_btn_opts = _img_button(MENU_TEX_CONTROL, MENU_BTN_Y[1], _menu_options)
_btn_quit = _img_button(MENU_TEX_EXIT,    MENU_BTN_Y[2], _menu_quit)
_opt_note = Text('what did you expect?', parent=camera.ui, position=(0.30, 0.20), scale=0.5,
                 color=RGB(111, 201, 112), enabled=False)
class TrophyScreen(Entity):
    def __init__(self):
        super().__init__()
        self.showing = False
        self.panel = Entity(parent=camera.ui, model='quad',
                            color=RGB(8, 6, 10, 236), scale=(2.0, 1.2),
                            z=-3.0, enabled=False)
        # RAINBOW, and a new colour every time you open it - I made
        # the ending texts on CONTROL to have the comic sans font and rainbow colours.
        self.title = Text('', parent=camera.ui, origin=(0, 0),
                          position=(0, 0.34), scale=1.15,
                          color=rainbow_colour(), z=-3.05, enabled=False)
        self.hint = Text('', parent=camera.ui, origin=(0, 0),
                         position=(0, -0.34), scale=0.7,
                         color=rainbow_colour(), z=-3.05, enabled=False)
        self.plates = []
        # should be another button with the control texture to go back to the main menu. - il think of it later
        self.back_button = Button(parent=camera.ui,
                           texture=crunchy_texture(None, TROPHY_BACK_IMAGE),
                           scale=TROPHY_BACK_SIZE,
                           position=(0, TROPHY_BACK_Y),
                           color=color.white,
                           highlight_color=RGB(255, 230, 230),
                           z=-3.05, enabled=False)
        self.back_button.on_click = self.go_back
        self.back_label = Text('BACK TO MENU', parent=camera.ui, origin=(0, 0),
                               position=(0, TROPHY_BACK_Y - TROPHY_BACK_SIZE[1] / 2 - 0.035),
                               scale=0.6, color=rainbow_colour('back'),
                               z=-3.06, enabled=False)
        for part, order in ((self.panel, 900), (self.title, 901),
                            (self.hint, 901), (self.back_button, 904),
                            (self.back_label, 905)):
            ad_layer(part, order)

    def go_back(self):
        self.hide()
        try:
            if not _menu_open:
                _to_main_menu()
            else:
                _set_menu(True)
        except Exception as exc:
            print('!! back to menu failed:', exc)

    def toggle(self):
        if self.showing:
            self.hide()
        else:
            self.show()

    def hide(self):
        self.showing = False
        self.panel.enabled = False
        self.title.enabled = False
        self.hint.enabled = False
        self.back_button.enabled = False
        self.back_label.enabled = False
        for plate in self.plates:
            destroy(plate)
        self.plates = []

    def show(self):
        self.hide()
        self.showing = True
        got = [t for t in TROPHY_ORDER if t in SAVE.get('trophies', [])]
        self.panel.enabled = True
        self.title.enabled = True
        self.hint.enabled = True
        # the back button is part of the cabinet, so it comes up
        # with it whether or not there is anything on the shelf.
        self.back_button.enabled = True
        self.back_label.enabled = True
        self.back_label.color = rainbow_colour()
        # a fresh pair of colours every time the cabinet is opened
        self.title.color = rainbow_colour()
        self.hint.color = rainbow_colour()
        if not got:
            # it has to say exactly this: "No endings unlocked"
            self.title.text = TROPHY_NONE_TEXT
            self.hint.text = 'finish the game once and it will be here'
            return
        self.title.text = 'ENDINGS UNLOCKED   %d / %d' % (len(got),
                                                          len(TROPHY_ORDER))
        self.hint.text = 'press CONTROL again to close'
        # lay them out in a row, centred, whatever their real shapes are
        widths = []
        texs = []
        for name in got:
            tex = crunchy_texture(None, name, detail=FULL_DETAIL)
            texs.append(tex)
            aspect = 1.0
            if tex is not None and getattr(tex, 'height', 0):
                aspect = tex.width / tex.height
            widths.append(TROPHY_HEIGHT * aspect)
        total = sum(widths) + TROPHY_GAP * (len(widths) - 1)
        x = -total / 2.0
        for tex, w, name in zip(texs, widths, got):
            plate = Entity(parent=camera.ui, model='quad', texture=tex,
                           color=color.white if tex else RGB(90, 80, 80),
                           scale=(w, TROPHY_HEIGHT),
                           position=(x + w / 2, TROPHY_Y), z=-3.05)
            ad_layer(plate, 902)
            self.plates.append(plate)
            label = Text(TROPHY_LABELS.get(name, name), parent=camera.ui,
                         origin=(0, 0), scale=0.52,
                         position=(x + w / 2, TROPHY_Y - TROPHY_HEIGHT / 2 - 0.05),
                         color=rainbow_colour(name), z=-3.06)
            ad_layer(label, 903)
            self.plates.append(label)
            x += w + TROPHY_GAP
            if tex is None:
                print('!! trophy picture %s.png not found' % name)


trophy_screen = TrophyScreen()


_MENU_THINGS = [_menu_bg, _wm, _btn_play, _btn_opts, _btn_quit, _opt_note,
                _btn_mute] + _menu_paras
_menu_open = True


def _set_menu(open_):
    global _menu_open
    _menu_open = open_
    for m in _MENU_THINGS:
        m.enabled = open_
    _opt_note.enabled = False
    if open_:
        _scatter_menu_paragraphs()     # new random layout every time
    player.enabled = not open_
    mouse.locked = not open_
    if hands_rig:
        hands_rig.enabled = not open_
    if player_body:
        player_body.enabled = SHOW_BODY and not open_
    if open_:
        viewmodel.enabled = False
        crosshair.enabled = False
        if weapons:
            weapons.show(False)
    if _menu_music:
        if open_ and not _menu_music.playing:
            _menu_music.play()
        if not open_:
            _menu_music.stop()


class _MenuFlicker(Entity):
    def __init__(self):
        super().__init__()
        self.t = 0.0
        self.hold = random.uniform(0.1, 0.5)
        self.frames = ['menuhuman', 'menunormal', 'menugreen', 'menunaked', 'eye 1', 'eye 2']

    def update(self):
        if not _menu_open:
            return
        self.t += time.dt
        if self.t < self.hold:
            return
        self.t = 0
        _menu_bg.texture = random.choice(self.frames)
        self.hold = random.uniform(0.1, 0.5)


_flicker = _MenuFlicker()
PAUSE_BG_TEXTURE = 'SUITNEW_PAUSE'
PAUSE_BG_FLICKER = False
PAUSE_BG_KEEP_ASPECT = False
PAUSE_BG_SIZE = ((1.0 * 119 / 111, 1.0) if PAUSE_BG_KEEP_ASPECT else (2.0, 1.2))

_pause_tex = crunchy_texture(None, PAUSE_BG_TEXTURE, detail=FULL_DETAIL)
if _pause_tex is None:
    print('!! %s.png not found - the pause screen falls back to the '
          'old plate. Drop the file anywhere in the project.'
          % PAUSE_BG_TEXTURE)
pause_bg = Entity(parent=camera.ui, model='quad',
                  texture=_pause_tex if _pause_tex else 'menunormal',
                  scale=PAUSE_BG_SIZE, z=0.9, enabled=False)
pause_dim = Entity(parent=camera.ui, model='quad', color=RGB(0, 0, 0, 130),
                   scale=(2, 1.2), z=0.85, enabled=False)
# PAUSED in comic sans, three times the size, and a different rainbow colour
# every time I pause drawn from the same palette as the menu
PAUSE_TITLE_SCALE = 1.8 * 3.0        # three times what it was
PAUSE_BTN_Y       = 0.0              # all three on one line, mid screen
PAUSE_BTN_X       = (-0.52, 0.0, 0.52)   # continue / control / exit
PAUSE_BTN_SIZE    = (0.30, 0.24)     # square-ish, like the menu ones

pause_title = Text('PAUSED', parent=camera.ui, origin=(0, 0), position=(0, 0.30),
                   scale=PAUSE_TITLE_SCALE, color=RGB(220, 220, 225),
                   enabled=False)
_paused_menu = False


def _pause_button(tex, x, action, label):
    b = Button(parent=camera.ui, texture=tex, scale=PAUSE_BTN_SIZE,
               position=(x, PAUSE_BTN_Y), color=color.white,
               highlight_color=RGB(255, 230, 230), enabled=False)
    b.on_click = action
    return b


def _resume():
    set_paused_menu(False)


def _to_main_menu():
    show_control_flash()
    set_paused_menu(False)
    voice.stop()
    game.clear_scenes()
    game.state = 'menu'
    fade.alpha = 0
    _set_menu(True)


class _PauseFlicker(Entity):
    def __init__(self):
        super().__init__()
        self.t = 0.0
        self.hold = random.uniform(0.1, 0.5)

    def update(self):
        if not _paused_menu:
            return
        self.t += time.dt
        if self.t < self.hold:
            return
        self.t = 0
        # the pause plate no longer flickers i took it out
        if PAUSE_BG_FLICKER:
            pause_bg.texture = random.choice(_flicker.frames)
        self.hold = random.uniform(0.1, 0.5)


def set_paused_menu(on):
    global _paused_menu
    if _menu_open:                      # already on the title screen
        return

    if globals().get('death_screen') is not None and death_screen.showing:
        return
    _paused_menu = on
    application.paused = on
    mouse.locked = not on
    for e in _PAUSE_THINGS:
        e.enabled = on
#pause glitch with the hands, fixed finally
    if on:
        if hands_rig:
            hands_rig.enabled = False
        if gun_hands:
            gun_hands.enabled = False
        if weapons:
            weapons.show(False)
    else:
        show_viewmodel(player.holding)
    crosshair.enabled = not on and game.state in ('doom', 'finale')
    if on:
        # comic sans, and a new rainbow colour every single time
        global SUB_FONT
        if SUB_FONT is None:
            SUB_FONT = comic_font() or ''
        if SUB_FONT:
            try:
                pause_title.font = SUB_FONT
            except Exception:
                pass
        pause_title.color = random.choice(MENU_RAINBOW)
        pause_title.scale = PAUSE_TITLE_SCALE
        if open_ads:
            pause_title.text = 'PAUSED   -   %d ad%s to close' % (
                len(open_ads), '' if len(open_ads) == 1 else 's')
            show_ad_hint()
        else:
            pause_title.text = 'PAUSED'
# the pause menu gets the same three pictures as the title screen
_btn_resume = _pause_button(MENU_TEX_PLAY,    PAUSE_BTN_X[0], _resume, 'resume')
_btn_menu   = _pause_button(MENU_TEX_CONTROL, PAUSE_BTN_X[1], _to_main_menu,
                            'main menu')
_btn_pquit  = _pause_button(MENU_TEX_EXIT,    PAUSE_BTN_X[2], _menu_quit, 'quit')
_PAUSE_THINGS = [pause_dim, pause_bg, pause_title,
                 _btn_resume, _btn_menu, _btn_pquit]
_pause_flicker = _PauseFlicker()

_set_menu(True)          # start on the menu with the player switched off

# THE APARTMENT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
apartment_door_inside = None
apartment_door_outside = None


def build_apartment():
    global apartment_door_inside
    w, h, d = APARTMENT_SIZE

    def tex(name, why):
        t = crunchy_texture(None, name)
        if t is None:
            print('!! apartment: %s.png not found (%s) - that surface will be '
                  'flat grey' % (name, why))
        return t

    floor_tex = tex(APARTMENT_FLOOR, 'the floor')
    wall_tex = tex(APARTMENT_WALL, 'the walls')

    ceil_tex = crunchy_texture(None, APARTMENT_CEILING)
    if ceil_tex is None:
        print('!! %s.png is not in the project - the apartment '
              'ceiling falls back to %r. Drop the file anywhere under the '
              'project folder and it appears, nothing else to change.'
              % (APARTMENT_CEILING, APARTMENT_CEILING_FALLBACK))
        ceil_tex = tex(APARTMENT_CEILING_FALLBACK, 'the ceiling')
    else:
        print('   apartment ceiling: %s' % APARTMENT_CEILING) # fallback

    # floor. csome random texture i made once again
    f = Entity(parent=apartment_root, model='cube', position=(0, -0.05, 0),
               scale=(w, 0.1, d), texture=floor_tex,
               color=color.white if floor_tex else RGB(30, 28, 32),
               unlit=True, collider='box')
    f.texture_scale = APARTMENT_FLOOR_TILE

    # ceiling crazy stuff honestly but very funny radiohead referance actually
    c = Entity(parent=apartment_root, model='cube', position=(0, h + 0.05, 0),
               scale=(w, 0.1, d), texture=ceil_tex,
               color=color.white if ceil_tex else RGB(40, 38, 42), unlit=True)
    c.texture_scale = APARTMENT_CEILING_TILE

    for px, pz, sx, sz in ((0, -d / 2, w, 0.2), (0, d / 2, w, 0.2),
                           (-w / 2, 0, 0.2, d), (w / 2, 0, 0.2, d)):
        wall = Entity(parent=apartment_root, model='cube',
                      position=(px, h / 2, pz), scale=(sx, h, sz),
                      texture=wall_tex,
                      color=color.white if wall_tex else RGB(70, 66, 72),
                      unlit=True, collider='box')
        wall.texture_scale = APARTMENT_WALL_TILE

    for name, wall, along, lift, size in APARTMENT_PICTURES:
        t = tex(name, 'a picture on the wall')
        if wall in ('n', 's'):
            zz = (-d / 2 + 0.12) if wall == 'n' else (d / 2 - 0.12)
            pos, rot = Vec3(along, lift, zz), (0, 180 if wall == 'n' else 0, 0)
        else:
            xx = (-w / 2 + 0.12) if wall == 'w' else (w / 2 - 0.12)
            pos, rot = Vec3(xx, lift, along), (0, -90 if wall == 'w' else 90, 0)
        Entity(parent=apartment_root, model='quad', position=pos, rotation=rot,
               scale=size, texture=t,
               color=color.white if t else RGB(120, 110, 115),
               unlit=True, double_sided=True)

    # THE DOOR, inside. Same size as every other door in the game, so it
    # reads as one of the village doors from either side, very convenient
    dtex = tex(APARTMENT_DOOR_TEX, 'the apartment door')
    dz = (-d / 2 + 0.14) * (1 if APARTMENT_DOOR_ON_Z < 0 else -1)
    dz = (-d / 2 + 0.14) if APARTMENT_DOOR_ON_Z < 0 else (d / 2 - 0.14)
    apartment_door_inside = Entity(
        parent=apartment_root, model='quad',
        position=Vec3(APARTMENT_DOOR_X, APARTMENT_DOOR_SIZE[1] / 2, dz),
        # 180 on the -z wall  hence FOR RENT was backwards, very annoying...
        rotation=(0, 180 if APARTMENT_DOOR_ON_Z < 0 else 0, 0),
        scale=APARTMENT_DOOR_SIZE, texture=dtex,
        color=color.white if dtex else RGB(150, 120, 110),
        unlit=True, double_sided=True, collider='box')
    apartment_door_inside.is_apartment_door = True

    # THE LATE RENT NOTICE - honstly i didnt fix it its still floating in the air..
    rent = crunchy_texture(None, APARTMENT_RENT_TEXTURE)
    if rent is None:
        print('!! %s.png not found - no late rent notice on the desk'
              % APARTMENT_RENT_TEXTURE)
    else:
        Entity(parent=office_root, model='quad', texture=rent,
               position=APARTMENT_RENT_POS, rotation=(90, 0, APARTMENT_RENT_TURN),
               scale=APARTMENT_RENT_SIZE, color=color.white,
               unlit=True, double_sided=True)

    # THE BED

    if APARTMENT_BED_ON:
        bed_holder = Entity(parent=apartment_root,
                            position=APARTMENT_BED_AT,
                            rotation=(0, APARTMENT_BED_YAW, 0))

        bed = Entity(parent=bed_holder, model=APARTMENT_BED_GLB,
                     scale=APARTMENT_BED_SCALE, double_sided=True,
                     unlit=True)
        make_fog_proof(bed)
        if bed.model is None:
            print('!! %s.glb would not load - no bed in the apartment'
                  % APARTMENT_BED_GLB)
            destroy(bed_holder)
        else:

            try:
                b = bed.getTightBounds(bed_holder)
                bed.y -= b[0][1]
            except Exception as exc:
                print('!! could not measure the bed (%s) - placed as-is' % exc)
            # you can lie on it, not walk through it
            Entity(parent=bed_holder, model='cube', collider='box',
                   visible=False, position=(0, 0.3, 0), scale=(2.05, 0.6, 0.9))
            at = bed_holder.world_position

            try:
                bb = bed.getTightBounds(bed_holder)
                w = bb[1][0] - bb[0][0]
                h = bb[1][1] - bb[0][1]
                dpt = bb[1][2] - bb[0][2]
                size = '%.2f x %.2f x %.2fm' % (w, h, dpt)
            except Exception:
                size = 'unmeasured'
            print('   bed: %s at world (%.2f, %.2f, %.2f), %s, turned %d '
                  'degrees, unlit so it actually draws'
                  % (APARTMENT_BED_GLB, at.x, at.y, at.z, size,
                     APARTMENT_BED_YAW))
    if OFFICE_IN_APARTMENT:
        office_root.parent = apartment_root
        office_root.position = APARTMENT_DESK_POS
        office_root.rotation_y = APARTMENT_DESK_ROT
        # the black slab with my picture on it is not needed - the FLOOR is
        # that picture now, which is what i wanted
        office_pad.enabled = False
        office_pad_face.enabled = False
        office_pad.collider = None
    print('apartment: %.1f x %.1f x %.1fm, floor %r, walls %r, %d pictures, '
          'desk moved in' % (w, h, d, APARTMENT_FLOOR, APARTMENT_WALL,
                             len(APARTMENT_PICTURES)))

build_apartment()


def build_apartment_entry():
    global apartment_door_outside
    dtex = crunchy_texture(None, APARTMENT_DOOR_TEX)
    p = APARTMENT_EXIT_TO

    apartment_door_outside = Entity(
        parent=city_root, model='quad',
        position=Vec3(p.x, p.y + APARTMENT_DOOR_SIZE[1] / 2, p.z),
        rotation=(0, APARTMENT_EXIT_FACE, 0), scale=APARTMENT_DOOR_SIZE,
        texture=dtex, color=color.white if dtex else RGB(150, 120, 110),
        unlit=True, double_sided=True, collider='box')
    apartment_door_outside.is_apartment_entry = True
    label = Text('HOME', parent=city_root, billboard=True, origin=(0, 0),
                 position=Vec3(p.x, p.y + APARTMENT_DOOR_SIZE[1] + 0.3, p.z),
                 scale=HOUSE_NUMBER_SCALE * 0.8, color=RGB(255, 240, 90))
    label.setFogOff(1)
    print('apartment: the way back in is at (%.2f, %.2f, %.2f) in the village'
          % (p.x, p.y, p.z))


build_apartment_entry()


# THE THRONE ROOM one of the bad endings room

throne_root = Entity(enabled=False, position=ROOM_THRONE_AT)
throne_exit_door = None

def bake_floor_grid(tris, step, stand_max, up_dot=0.55):
    cells, lo = {}, None
    for a, b, c in tris:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        wx, wy, wz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx = uy * wz - uz * wy
        ny = uz * wx - ux * wz
        nz = ux * wy - uy * wx
        L = math.sqrt(nx * nx + ny * ny + nz * nz)
        if L < 1e-12 or ny / L < up_dot:
            continue                       # not something you can stand on
        top = max(a[1], b[1], c[1])
        if top > stand_max:
            continue                       # the top of a wall, not a floor
        lo = top if lo is None else min(lo, top)
        x0 = min(a[0], b[0], c[0]); x1 = max(a[0], b[0], c[0])
        z0 = min(a[2], b[2], c[2]); z1 = max(a[2], b[2], c[2])
        for ix in range(int(math.floor(x0 / step)), int(math.floor(x1 / step)) + 1):
            for iz in range(int(math.floor(z0 / step)), int(math.floor(z1 / step)) + 1):
                k = (ix, iz)
                if top > cells.get(k, -1e18):
                    cells[k] = top
    if not cells:
        return None, None
    ixs = [k[0] for k in cells]; izs = [k[1] for k in cells]
    verts = []
    for ix in range(min(ixs), max(ixs) + 1):
        for iz in range(min(izs), max(izs) + 1):
            y = cells.get((ix, iz), lo)     # holes get the lowest real floor
            ax, az = ix * step, iz * step
            bx, bz = ax + step, az + step
            p00 = (ax, y, az); p10 = (bx, y, az)
            p01 = (ax, y, bz); p11 = (bx, y, bz)
            verts += [p00, p11, p10, p00, p01, p11]
    bounds = (min(ixs) * step, (max(ixs) + 1) * step,
              min(izs) * step, (max(izs) + 1) * step, lo)
    return verts, bounds


def build_throne_room():
    global throne_exit_door
    holder = Entity(parent=throne_root, scale=ROOM_THRONE_SCALE)

    # COMPLETELY RANDOM TEXTURES IN HERE - USED AI - because i coudlnt figure out how to make the triangles smaller
    #it keeps being super laggy
    room = None
    if ROOM_THRONE_CHAOS:
        path = find_asset(ROOM_THRONE_GLB + '.glb')
        try:
            groups = read_glb_by_material(path) if path else {}
        except Exception as e:
            print('!! throne room: could not split by material (%s), loading '
                  'it whole' % e)
            groups = {}
        if groups:

            all_tris = []
            for mat, (vlist, ulist) in groups.items():
                for t in range(0, len(vlist) - 2, 3):
                    a, b, c = vlist[t], vlist[t + 1], vlist[t + 2]
                    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
                    wx, wy, wz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
                    nx = uy * wz - uz * wy
                    ny = uz * wx - ux * wz
                    nz = ux * wy - uy * wx
                    area = nx * nx + ny * ny + nz * nz     # squared, fine
                    all_tris.append((area, mat, t))
            if ROOM_THRONE_KEEP < 1.0 and all_tris:
                all_tris.sort(key=lambda r: -r[0])
                keep_n = max(60, int(len(all_tris) * ROOM_THRONE_KEEP))
                dropped = len(all_tris) - keep_n
                all_tris = all_tris[:keep_n]
                print('   throne room: kept the largest %d triangles, '
                      'dropped %d small ones' % (keep_n, dropped))
            keep_set = set((mat, t) for _a, mat, t in all_tris)

            cells = {}
            for mat, (vlist, ulist) in groups.items():
                for t in range(0, len(vlist) - 2, 3):
                    if (mat, t) not in keep_set:
                        continue
                    tri = (vlist[t], vlist[t + 1], vlist[t + 2])
                    uvs = (ulist[t], ulist[t + 1], ulist[t + 2])
                    cx_ = sum(v[0] for v in tri) / 3.0
                    cy_ = sum(v[1] for v in tri) / 3.0
                    cz_ = sum(v[2] for v in tri) / 3.0
                    key = (int(cx_ // ROOM_THRONE_CHAOS_CHUNK),
                           int(cy_ // ROOM_THRONE_CHAOS_CHUNK),
                           int(cz_ // ROOM_THRONE_CHAOS_CHUNK))
                    cv, cu = cells.setdefault(key, ([], []))
                    cv.extend(tri)
                    cu.extend(uvs)
            for key, (cv, cu) in sorted(cells.items()):
                # seeded off the cell's own coordinates, so it is identical
                # every run and you can tell me which patch to change
                seed = (key[0] * 73856093) ^ (key[1] * 19349663) ^ (key[2] * 83492791)
                name = ROOM_THRONE_CHAOS_SKINS[abs(seed) % len(ROOM_THRONE_CHAOS_SKINS)]
                tscale = ROOM_THRONE_CHAOS_SCALES[abs(seed >> 8)
                                                  % len(ROOM_THRONE_CHAOS_SCALES)]
                tex = crunchy_texture(None, name)
                if tex is None:
                    print('!! throne room texture missing: %s' % name)
                piece = Entity(parent=holder,
                               model=Mesh(vertices=cv, uvs=cu,
                                          mode='triangle', static=True),
                               texture=tex,
                               color=color.white if tex else RGB(150, 140, 150),
                               double_sided=True, unlit=ROOM_THRONE_UNLIT)
                piece.texture_scale = tscale
            room = holder            # something was built, so it is not empty
            print('throne room: %d materials cut into %d chunks, every chunk a '
                  'different texture' % (len(groups), len(cells)))

    if room is None:
        room = Entity(parent=holder, model=ROOM_THRONE_GLB,
                      unlit=ROOM_THRONE_UNLIT, double_sided=True)
    # measured off the file: 12.0 wide, 5.9 tall, 12.2 deep, already in metres
    bx0, bx1, bz0, bz1, by0, by1 = -6.0, 6.0, -6.1, 6.1, 0.0, 5.9

    if getattr(room, 'model', None) is None and room is not holder:
        print('!! %s.glb did not load - the throne room will be an empty void'
              % ROOM_THRONE_GLB)
        Entity(parent=holder, model='cube', collider='box', visible=False,
               position=(0, -0.5, 0), scale=(14, 1, 14))
    else:
        path = find_asset(ROOM_THRONE_GLB + '.glb')
        try:
            started = time.time()
            tris = read_glb_triangles(path)
            xs = [v[0] for t in tris for v in t]
            ys = [v[1] for t in tris for v in t]
            zs = [v[2] for t in tris for v in t]
            bx0, bx1 = min(xs), max(xs)
            by0, by1 = min(ys), max(ys)
            bz0, bz1 = min(zs), max(zs)

            if ROOM_THRONE_MESH_COLLIDER:

                Entity(parent=holder,
                       model=Mesh(vertices=[v for t in tris for v in t],
                                  mode='triangle', static=True),
                       collider='mesh', visible=False)
                print('throne room: FULL mesh collider, %d triangles - this is '
                      'the slow one, set ROOM_THRONE_MESH_COLLIDER = False'
                      % len(tris))
            else:
                floor, fb = bake_floor_grid(tris, ROOM_THRONE_GRID,
                                            by0 + ROOM_THRONE_STAND_MAX)
                if floor:
                    Entity(parent=holder,
                           model=Mesh(vertices=floor, mode='triangle',
                                      static=True),
                           collider='mesh', visible=False)
                    print('throne room: floor baked to %d collision triangles '
                          'from %d (%.0fx less to test every frame), %.1fm '
                          'cells, in %.2fs'
                          % (len(floor) // 3, len(tris),
                             len(tris) / max(1, len(floor) // 3),
                             ROOM_THRONE_GRID, time.time() - started))
                else:
                    print('!! throne room: nothing upward-facing under %.1fm - '
                          'flat floor instead' % ROOM_THRONE_STAND_MAX)
                    Entity(parent=holder, model='cube', collider='box',
                           visible=False,
                           position=((bx0 + bx1) / 2, by0 - 0.5, (bz0 + bz1) / 2),
                           scale=(bx1 - bx0 + 2, 1, bz1 - bz0 + 2))
            print('   throne room: %.1f x %.1f x %.1fm, y %.2f..%.2f'
                  % (bx1 - bx0, by1 - by0, bz1 - bz0, by0, by1))
        except Exception as exc:
            print('!! throne room collision failed (%s) - flat floor only' % exc)
            Entity(parent=holder, model='cube', collider='box', visible=False,
                   position=(0, -0.5, 0), scale=(14, 1, 14))
#the models open on one slide i just put a colldier there and didnt tryand make the wall appear out of nowhere it just wasnt working
    if ROOM_THRONE_WALLS:
        pad = ROOM_THRONE_WALL_PAD
        t = 1.0
        cx, cz = (bx0 + bx1) / 2, (bz0 + bz1) / 2
        w, d = (bx1 - bx0) - pad * 2, (bz1 - bz0) - pad * 2
        h = max(3.0, (by1 - by0))
        for px, pz, sx, sz in ((bx0 + pad - t / 2, cz, t, d + t * 2),
                               (bx1 - pad + t / 2, cz, t, d + t * 2),
                               (cx, bz0 + pad - t / 2, w + t * 2, t),
                               (cx, bz1 - pad + t / 2, w + t * 2, t)):
            Entity(parent=holder, model='cube', collider='box', visible=False,
                   position=(px, by0 + h / 2, pz), scale=(sx, h + 4, sz))
        Entity(parent=holder, model='cube', collider='box', visible=False,
               position=(cx, by1 + 0.5, cz), scale=(w + 4, 1, d + 4))
        print('   throne room: sealed with 4 walls + a lid inside %.1f x %.1fm '
              '- you cannot walk out into the void any more' % (w, d))

    #doooor
    _tsize = room_exit_door_size(4)
    _ttex = crunchy_texture(None, room_exit_door_texture(4))
    throne_exit_door = Entity(
        parent=throne_root, model='quad',
        position=Vec3(ROOM_THRONE_EXIT.x, by0 + _tsize[1] / 2, ROOM_THRONE_EXIT.z),
        rotation=(0, ROOM_THRONE_EXIT_YAW, 0),
        scale=_tsize, texture=_ttex,
        color=color.white if _ttex else RGB(150, 120, 110),
        unlit=True, double_sided=True, collider='box')
    throne_exit_door.is_throne_exit = True


build_throne_room()
build_plot()
build_fantasy_house()

# THE DEATH SCREEN

# EVERYTHING ABOUT IT IS DRAWN THE WAY THE ADVERTS ARE - the 'fixed' bin,
# depth testing off, fog off - which is the only way to be certain that nothing
# in the game can end up in front of it.
class DeathScreen(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)
        self.showing = False
        self.then = None
        self.backing = Entity(parent=camera.ui, model='quad', color=color.black,
                              scale=(3, 2), z=-4.30, unlit=True, enabled=False)
        self.picture = Entity(parent=camera.ui, model='quad', color=color.white,
                              z=-4.35, unlit=True, enabled=False)
        self.button = Button(parent=camera.ui, model='quad',
                             color=color.white,
                             highlight_color=RGB(255, 150, 150),
                             pressed_color=RGB(255, 90, 90),
                             z=-4.40, enabled=False)
        self.button.on_click = self.dismiss
        self.line_shadow = Text('', parent=camera.ui, origin=(0, 0), z=-4.44,
                                color=RGB(0, 0, 0, 210), enabled=False)
        self.line = Text('', parent=camera.ui, origin=(0, 0), z=-4.46,
                         enabled=False)
        self.hint = Text('', parent=camera.ui, origin=(0, 0), z=-4.46,
                         scale=0.62, color=RGB(210, 200, 190, 190),
                         enabled=False)
        for part, order in ((self.backing, 900), (self.picture, 901),
                            (self.button, 902), (self.line_shadow, 903),
                            (self.line, 904), (self.hint, 904)):
            ad_layer(part, order)

    @property
    def widgets(self):
        return (self.backing, self.picture, self.button, self.line_shadow,
                self.line, self.hint)

    def fit_full_screen(self, tex):
        screen_w, screen_h = window.aspect_ratio, 1.0
        if tex is None:
            return Vec2(screen_w, screen_h)
        img = tex.width / max(1, tex.height)
        if img > screen_w / screen_h:          # wider than the screen
            h, w = screen_h, screen_h * img
        else:                                  # taller than the screen
            w, h = screen_w, screen_w / img
        w = max(screen_w, lerp(w, screen_w, DEATH_STRETCH))
        h = max(screen_h, lerp(h, screen_h, DEATH_STRETCH))
        return Vec2(w, h)

    def show(self, then=None, hint='[E]  or click'):
        if self.showing:
            return
        self.showing = True
        self.then = then

        # the picture
        name = random.choice(DEATH_SCREENS)
        tex = crunchy_texture(None, name)
        if tex is None:
            print('!! death screen %r not found - put %s.jpg anywhere in the '
                  'project. Falling back to plain black.' % (name, name))
        self.picture.texture = tex
        self.picture.color = color.white if tex else RGB(12, 8, 10)
        size = self.fit_full_screen(tex)
        self.picture.scale = (size.x, size.y)
        self.picture.position = (0, 0)

        # the control picture, as the button, in the middle
        btn = crunchy_texture(None, DEATH_BUTTON_IMAGE)
        if btn is None:
            print('!! %s.png not found - the button will be a plain white '
                  'square, it still works' % DEATH_BUTTON_IMAGE)
        self.button.texture = btn
        bh = DEATH_BUTTON_HEIGHT
        bw = bh * (btn.width / max(1, btn.height)) if btn else bh
        self.button.scale = (bw, bh)
        self.button.position = DEATH_BUTTON_POS

        # and the line
        global SUB_FONT
        if SUB_FONT is None:
            SUB_FONT = comic_font() or ''
        words = wrap_text(random.choice(DEATH_LINES), DEATH_TEXT_WRAP)
        spot = random.choice(DEATH_TEXT_SPOTS)
        scale = random.uniform(*DEATH_TEXT_SCALE)
        for t in (self.line_shadow, self.line):
            t.text = words
            t.scale = scale
            t.position = spot
        self.line.color = random.choice(DEATH_TEXT_COLOURS)
        self.line_shadow.position = (spot[0] + 0.006, spot[1] - 0.006)
        if SUB_FONT:
            for t in (self.line, self.line_shadow):
                try:
                    t.font = SUB_FONT
                except Exception:
                    pass
        self.hint.text = hint
        self.hint.position = (DEATH_BUTTON_POS[0],
                              DEATH_BUTTON_POS[1] - DEATH_BUTTON_HEIGHT / 2 - 0.045)

        clear_all_ads()
        talk_box.close()
        prompt_box.hide()
        handler_head.hide()
        show_prompt('')
        set_hud(False)
        crosshair.enabled = False
        if hands_rig:
            hands_rig.enabled = False
        if weapons:
            weapons.show(False)
        player.enabled = False
        mouse.locked = False
        application.paused = True
        fade.alpha = 0
        for part in self.widgets:
            part.enabled = True

    def hide(self):
        self.showing = False
        for part in self.widgets:
            part.enabled = False
        application.paused = False
        mouse.locked = True
        player.enabled = True

    def dismiss(self):
        if not self.showing:
            return
        then, self.then = self.then, None
        self.hide()
        beep(pitch=-14, length=0.2, wave='square', volume=0.3)
        if then:
            then()

    def input(self, key):
        # ignore_paused, so this keeps working while the game is frozen - the
        # same trick esc_handler uses, and for the same reason
        if not self.showing:
            return
        if key in ('e', 'enter', 'space', 'return'):
            self.dismiss()

death_screen = DeathScreen()


class ViewmodelGuard(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)

    def update(self):
        hiding = (_menu_open or _paused_menu
                  or (globals().get('death_screen') is not None
                      and death_screen.showing))
        if not hiding:
            return
        if hands_rig is not None and hands_rig.enabled:
            hands_rig.enabled = False
        if gun_hands is not None and gun_hands.enabled:
            gun_hands.enabled = False
        if held_phone is not None and held_phone.enabled:
            held_phone.enabled = False
        if viewmodel.enabled:
            viewmodel.enabled = False
        if crosshair.enabled:
            crosshair.enabled = False
        if weapons is not None:
            for gun in weapons.guns:
                if gun.enabled:
                    gun.enabled = False


viewmodel_guard = ViewmodelGuard()

# THE CEO OF THE UNIVERSE
class CeoScreen(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)
        self.showing = False
        self.then = None
        self.black = Entity(parent=camera.ui, model='quad', color=color.black,
                            scale=(3, 2), z=-4.50, unlit=True, enabled=False)
        self.picture = Entity(parent=camera.ui, model='quad', color=color.white,
                              z=-4.52, unlit=True, enabled=False)
        self.button = Button(parent=camera.ui, model='quad', color=color.white,
                             highlight_color=RGB(255, 150, 150),
                             pressed_color=RGB(255, 90, 90),
                             z=-4.60, enabled=False)
        self.button.on_click = self.dismiss
        self.hint = Text('', parent=camera.ui, origin=(0, 0), z=-4.62,
                         scale=0.62, color=RGB(215, 205, 195, 210),
                         enabled=False)
        for part, order in ((self.black, 250), (self.picture, 251),
                            (self.button, 950), (self.hint, 951)):
            ad_layer(part, order)
        self.plates = []
        self.plate_at = 0
        self.plate_timer = CEO_PICTURE_SWAP

    def show(self):
        if self.showing:
            return
        self.showing = True
        # HERES WHICH PICTURES ARE ACTUALLY IN THE PROJECT

        self.plates = []
        for name in CEO_PICTURES:
            got = crunchy_texture(None, name, detail=FULL_DETAIL)
            if got is not None:
                self.plates.append(got)
        if not self.plates:
            got = crunchy_texture(None, CEO_PICTURE, detail=FULL_DETAIL)
            if got is not None:
                self.plates.append(got)
        if not self.plates:
            print('!! none of %s or %s found - the CEO ending will be plain '
                  'black' % (CEO_PICTURES, CEO_PICTURE))
        self.plate_at = 0
        self.plate_timer = CEO_PICTURE_SWAP
        tex = self.plates[0] if self.plates else None
        self.picture.texture = tex
        self.picture.color = color.white if tex else RGB(20, 10, 8)
        # FULL SCREEN
        if CEO_PICTURE_FULLSCREEN:
            self.picture.scale = (2.0, 1.2)
            self.picture.position = (0, 0)
        else:
            h = CEO_PICTURE_HEIGHT
            w = h * ((tex.width / max(1, tex.height)) if tex is not None else 0.85)
            self.picture.scale = (w, h)
            self.picture.position = CEO_PICTURE_POS

        btn = crunchy_texture(None, CEO_BUTTON_IMAGE)
        if btn is None:
            print('!! %s.png not found - the button back to the menu will be a '
                  'plain white square. It still works.' % CEO_BUTTON_IMAGE)
        self.button.texture = btn
        bh = CEO_BUTTON_HEIGHT
        bw = bh * (btn.width / max(1, btn.height)) if btn else bh
        self.button.scale = (bw, bh)
        self.button.position = CEO_BUTTON_POS
        self.hint.text = CEO_BUTTON_HINT
        self.hint.position = (CEO_BUTTON_POS[0], CEO_BUTTON_POS[1] - bh / 2 - 0.04)

        self.button.enabled = False        # not until the speech is finished
        self.hint.enabled = False
        self.black.enabled = True
        self.picture.enabled = True

    def offer_button(self):
        if not self.showing:
            return
        self.button.enabled = True
        self.hint.enabled = True
        beep(pitch=-4, length=0.22, wave='sine', volume=0.35)

    def go_black(self):
        self.picture.enabled = False
        self.black.enabled = True

    def dismiss(self):
        if not self.showing:
            return
        then, self.then = self.then, None
        beep(pitch=-14, length=0.2, wave='square', volume=0.3)
        if then:
            then()

    def hide(self):
        self.showing = False
        self.then = None
        self.black.enabled = False
        self.picture.enabled = False
        self.button.enabled = False
        self.hint.enabled = False

ceo_screen = CeoScreen()


# GAME STATE MACHINE - scenes and endings!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
class Game(Entity):
    def __init__(self):
        super().__init__()
        self.state = 'menu'
        self.chapter = 0             # which voice note we're up to
        self.level_index = 0         # which entry in LEVELS we're up to
        self.enemies = []
        self.enemy_queue = []
        self.kills = 0
        self.livers = 0               # the running total, never reset
        self.pickups = []
        self.health_packs = []
        self.fireballs = []           # every round in the air
        self.boss = None
        self.key = None
        self.exit_door = None
        self.exit_door_big = None     # the wall-sized one, see EXIT_BIG_SPOT
        self.has_key = False
        self.phone_ringing = False
        self.ring_timer = 0
        self.office_pull = 1.0      # 1 at the desk, 0 out in the cemetery
        self.outside_now = False
        self.doom_timer = 0
        self.door_open = False
        self.finale_choice_ready = False
        self.ending_running = False
        # THE THANKS CARD
        self.credits_after_thanks = False
        # True once the DOOM boss has been killed.
        self.boss_killed = False
        # True only while the pacifist "the house is yours" ending is running.
        self.happy_ending = False
        # True once you have shot the scientist.
        self.scientist_dead = False
        self.survived = False        # lasted the last level out
        self.signed = False          # signed the lease at the end
        self.pacifist_offer = False  # killed nobody, walked out
        self.lease_signed = False    # the scientist signed for you
        self.bought_house = False    # shot him, bought door 5
        self.campaign_done = False
        self.lease_from_dj = False
        self.boss_killed = False     # the CEO of the universe
        self.enemies_awake = False
        # False until you reach the key area, at which point the whole
        # wave is created at once. See release_enemies().
        self.enemies_released = False
        self.voices_played = set()   # so a chapter never plays twice on a retry
        self.house_return = None     # where you reappear after leaving a house
        self.house_at = -1
        self.houses_visited = set()
        self.house_grace = 0.0

    # scene switching
    def clear_scenes(self):
        if doom_music and doom_music.playing:
            doom_music.stop()
        self.stop_ring()                 # no alarm in the next scene
        office_root.enabled = False
        apartment_root.enabled = False
        throne_root.enabled = False
        doom_root.enabled = False
        garden_root.enabled = False
        if plot_exit_door is not None:
            plot_exit_door.enabled = False
        sky.enabled = False
        city_root.enabled = False
        house_root.enabled = False       # the five NPC interiors
        clear_all_ads()                  # no adverts left over across a cut

        end_dialogue_camera(snap=True)
        # the happy ending's sky and music belong to that ending only
        self.happy_ending = False
        talk_box.close()
        stop_all_voice_clips()
        self.kill_all_enemies()
        self.clear_level_objects()
        show_prompt('')
        set_hud(False)
        crosshair.enabled = False

    def kill_all_enemies(self):
        for e in list(self.enemies):
            destroy(e)
        self.enemies = []

    def clear_level_objects(self):
        def kill(*things):
            for t in things:
                try:
                    if t is not None:
                        destroy(t)
                except Exception:
                    pass

        for pickup in list(self.pickups):
            kill(getattr(pickup, 'glow', None), getattr(pickup, 'label', None), pickup)
        self.pickups = []
        for pack in list(getattr(self, 'health_packs', [])):
            kill(getattr(pack, 'label', None), pack)
        self.health_packs = []
        for ball in list(getattr(self, 'fireballs', [])):
            kill(ball)
        self.fireballs = []
        if self.key:
            kill(getattr(self.key, 'halo', None), getattr(self.key, 'label', None), self.key)
            self.key = None
        for name in ('exit_door', 'exit_door_big'):
            d = getattr(self, name, None)
            if d:
                kill(getattr(d, 'sign', None), getattr(d, 'glow', None), d)
                setattr(self, name, None)
        self.has_key = False

    # OFFICE
    def begin(self):
        self.chapter = 0
        self.level_index = 0
        self.houses_visited = set()
        self.pacifist_offer = False
        self.lease_signed = False
        self.bought_house = False
        self.campaign_done = False
        self.lease_from_dj = False
        self.boss_killed = False
        self.voices_played = set()
        player.health = PLAYER_MAX_HP
        weapons.reset()
        self.livers = 0             # a new run starts empty
        refresh_livers()
        self.enter_apartment()

    def enter_apartment(self, ring=True):
        self.clear_scenes()
        self.state = 'apartment'
        apartment_root.enabled = True
        office_root.enabled = True
        city_root.enabled = False
        friend.enabled = False
        exit_door.enabled = False
        exit_label.enabled = False
        door_to_doom.enabled = False
        door_glow.enabled = False
        door_label.enabled = False

        set_scene_fog(False)
        set_clip('apartment')
        movement.set_base_speed(OFFICE_SPEED)
        movement.set_eye_height('apartment')
        player.speed = OFFICE_SPEED
        place_player(APARTMENT_AT + APARTMENT_SPAWN)
        player.rotation_y = APARTMENT_FACE
        player.camera_pivot.rotation_x = 0
        player.holding = 'hand'
        show_viewmodel('hand')
#only when new job is availbale handler shoudl call
        if ring:
            self.phone_ringing = True
            self.ring_timer = 0
            self.start_ring()
            self.door_open = False
            show_prompt('[E]  answer it')
        else:
            self.phone_ringing = False
            self.stop_ring()
            show_prompt('[E]  on the door to go back out')
        fade_from_black(1.2)

    def leave_apartment(self):
        if self.state != 'apartment':
            return
        if self.phone_ringing or voice.playing:
            flash_notice('answer the phone first')
            return
        if self.house_grace > 0:
            return
        self.house_grace = 0.8
        fade_to_black(0.5, then=self.enter_office)

    def enter_apartment_from_village(self):
        if self.state != 'office' or self.house_grace > 0:
            return
        self.house_grace = 0.8
        fade_to_black(0.5, then=lambda: self.enter_apartment(ring=False))

    def enter_throne_room(self):
        self.clear_scenes()
        self.state = 'throne'
        throne_root.enabled = True
        set_scene_fog(False)
        set_clip('throne')
        movement.set_base_speed(OFFICE_SPEED)
        movement.set_eye_height('throne')
        player.speed = OFFICE_SPEED
        place_player(ROOM_THRONE_AT + ROOM_THRONE_SPAWN)
        player.rotation_y = ROOM_THRONE_FACE
        player.camera_pivot.rotation_x = 0
        player.holding = 'hand'
        show_viewmodel('hand')
        show_prompt('')
        fade_from_black(2.0)
        invoke(self.say_ending, ENDING_EMPEROR, ROOM_THRONE_SPEAKER, delay=2.2)

    def leave_plot(self):
        if self.house_grace > 0:
            return
        self.house_grace = 1.0
        self.ending_running = False
        fade_to_black(0.8, then=self.enter_office)

    def leave_throne_room(self):
        if self.house_grace > 0:
            return
        self.house_grace = 0.8
        fade_to_black(0.6, then=self.enter_office)

    def say_ending(self, lines, who):
        show_prompt('')
        talk_box.start(lines, who)

    def ending_bought_house(self):
        show_prompt('')

        talk_box.start(ENDING_BOUGHT + ENDING_EMPEROR, 'THE DEED',
                       on_finish=thanks_card_after)
        if not ENDING_EXPLORE:
            invoke(self.roll_credits, delay=3.0 + 3.4 * len(ENDING_BOUGHT))

    def ending_owned(self):
        if self.ending_running:
            return
        self.ending_running = True
        show_prompt('')


        # THIS IS THE HAPPY ENDING
        fade_to_black(1.2,
                      then=lambda: self._go_garden(then_sign=False, happy=True))
        invoke(self._say_owned, delay=2.6)

    def _say_owned(self):
        stop_all_voice_clips()
        talk_box.start(ENDING_OCEAN, 'THE LEASE', voice_clip=None,
                       on_finish=thanks_card_after)
        if not ENDING_EXPLORE:
            invoke(self.roll_credits, delay=3.0 + 3.4 * len(ENDING_OCEAN))

    def enter_office(self):
        self.clear_scenes()
        self.state = 'office'
        office_root.enabled = False
        apartment_root.enabled = False
        friend.enabled = False
        exit_door.enabled = False
        exit_label.enabled = False

        door_to_doom.enabled = self.door_open
        door_glow.enabled = self.door_open
        door_label.enabled = DOOM_DOOR_LABEL and self.door_open

        # no fog in the village, i tried it and it looked wrong
        set_scene_fog(False)
        set_clip('office')

        city_root.enabled = True
        self.office_pull = 1.0
        self.outside_now = False
        movement.set_base_speed(OFFICE_SPEED)
        movement.set_eye_height('office')
        player.speed = OFFICE_SPEED

        place_player(Vec3(APARTMENT_STEP_OUT))            # yours
        player.rotation_y = APARTMENT_EXIT_FACE + 180
        player.camera_pivot.rotation_x = 0
        player.holding = 'hand'
        show_viewmodel('hand')

        self.phone_ringing = False
        self.stop_ring()
        if self.door_open:
            show_prompt('find the red door and press [E]')
        else:
            show_prompt('')
        fade_from_black(1.2)

    def start_ring(self):
        ring = load_sound(RING_SOUND, loop=RING_LOOP, volume=RING_VOLUME)
        if ring is None:
            return
        ring.loop = RING_LOOP
        ring.volume = RING_VOLUME
        ring.play()

    def stop_ring(self):
        ring = _sound_cache.get(RING_SOUND)
        if ring is not None:
            ring.stop()

    def can_replay_call(self):
        if voice.playing or talk_box.open:
            return False
        if self.state == 'finale':
            return False
        return len(self.voices_played) > 0

    def answer_phone(self, replay=False):
        self.phone_ringing = False
        self.stop_ring()
        phone.color = PHONE_DIM          # stops ringing
        show_prompt('')
        hand_punch()

        if replay and self.voices_played:
            which = max(self.voices_played)
        else:
            which = self.chapter
        chapter_lines = CHAPTERS[min(which, len(CHAPTERS) - 1)]
        self.voices_played.add(which)
        if replay:
            print('   phone: replaying the call from chapter %d' % which)
        # the handset comes up into your hand for the duration of the call
        player.holding = 'phone'
        invoke(show_viewmodel, 'phone', delay=0.22)
        voice.play(chapter_lines,
                   on_finish=self.hang_up,
                   audio_name='voice_%d' % which,
                   chapter=which,
                   handler=True)

    def hang_up(self):
        player.holding = 'hand'
        show_viewmodel('hand')
        self.open_door()

    def go_to_doom(self):
        if self.state != 'office' or not self.door_open:
            return
        self.door_open = False
        show_prompt('')
        fade_to_black(0.9, then=self.enter_doom)

    def open_door(self):
        self.door_open = True
        door_to_doom.enabled = True
        door_glow.enabled = True
        door_label.enabled = DOOM_DOOR_LABEL
        door_label.text = (LEVELS[min(self.level_index, len(LEVELS) - 1)]['title']
                           if DOOM_DOOR_LABEL else '')
        show_prompt('find the red door and press [E]')

    # THE NPC HOUSES
    def enter_house(self, index):
        if self.state != 'office' or index >= len(village_houses):
            return
        if self.house_grace > 0:
            return
        locked = index in HOUSE_LOCKED_UNTIL
        need = HOUSE_LOCKED_UNTIL.get(index)
        if index == HOUSE_FORSALE_DOOR and self.bought_house:
            locked = False

        if DOOR5_NEEDS_CAMPAIGN and index == HOUSE_FORSALE_DOOR \
                and not self.campaign_done:
            show_prompt(DOOR5_LOCKED_MESSAGE)
            flash_title(DOOR5_LOCKED_MESSAGE, 1.8)
            beep(pitch=-18, length=0.14, wave='square', volume=0.3)
            self.house_grace = 0.6
            return

        if locked and (need is None or need not in self.houses_visited):
            show_prompt(HOUSE_LOCKED_MESSAGE)
            flash_title(HOUSE_LOCKED_MESSAGE, 1.6)
            beep(pitch=-18, length=0.14, wave='square', volume=0.3)
            self.house_grace = 0.6      # so holding E doesn't machine-gun it heheee
            return

        ensure_houses_built()
        if index >= len(house_rooms):
            print(f'!! house {index}: no interior was built, staying outside')
            return


        # ENDING_EXPLORE
        if index == HOUSE_FORSALE_DOOR:
            self.house_grace = 1.0
            self.bought_house = True
            self.lease_from_dj = True
            self.ending_running = False
            fade_to_black(0.8, then=self.enter_throne_room)
            return

        self.house_return = village_houses[index]['outside']
        self.house_at = index
        self.houses_visited.add(index)
        self.house_grace = 1.0
        self.state = 'house'

        self.house_room = village_houses[index]['room']
        room = house_rooms[village_houses[index]['room']]

        city_root.enabled = False
        office_root.enabled = False
        house_root.enabled = True
        talk_box.close()
        set_scene_fog(False)
        set_clip('house')

        movement.set_base_speed(HOUSE_SPEED)
        movement.set_eye_height('house')
        player.speed = HOUSE_SPEED
        place_player(room['spawn'])
        player.rotation_y = room['face']
        player.camera_pivot.rotation_x = 0
        player.holding = 'hand'
        show_viewmodel('hand')
        show_prompt('[E] on the door to leave  /  walk into it')
        fade_from_black(0.7)

    def leave_house(self):
        if self.state != 'house' or self.house_grace > 0:
            return
        self.house_grace = 1.0
        self.state = 'office'
        self.house_room = None     # the house music stops, when outside
        house_root.enabled = False
        city_root.enabled = True
        office_root.enabled = True
        set_clip('office')

        movement.set_eye_height('office')
        place_player(self.house_return)
        player.camera_pivot.rotation_x = 0
        player.holding = 'hand'
        show_viewmodel('hand')
        show_prompt('')
        fade_from_black(0.7)

    # DOOOOOOOOOOOOOOOMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
    def enter_doom(self):
        prepare_doom()
        if not doom_collision:
            print('!! no DOOM map loaded, skipping to the next chapter')
            self.finish_level()
            return

        self.clear_scenes()
        self.state = 'doom'
        doom_root.enabled = True

        level = LEVELS[min(self.level_index, len(LEVELS) - 1)]

        set_scene_fog(False)
        set_clip('doom')

        movement.set_base_speed(DOOM_SPEED)
        movement.set_eye_height('doom')
        player.speed = DOOM_SPEED
        place_player(snap_to_doom_floor(DOOM_SPAWN, 'player spawn'))
        player.rotation_y = 0
        player.camera_pivot.rotation_x = 0
        player.health = PLAYER_MAX_HP
        player.holding = 'gun'
        show_viewmodel('gun')
        refresh_health()
        set_hud(True)
        crosshair.enabled = True

        self.kills = 0
        self.doom_timer = 0
        self.has_key = False
        self.survived = False
        self.enemies_awake = True
        global _enemy_pool
        _enemy_pool = None

        self.place_key_and_exit()
        self.place_weapon_pickups(level)
        self.place_health_packs(level)
        self.boss = None

        self.enemies_released = not ENEMY_HOLD_UNTIL_KEY
        if self.enemies_released:
            self.populate_level(level)
        else:
            key_at = self.key.world_position if self.key else DOOM_SPAWN
            print('   DOOM: level is empty until you get within %.0fm of the '
                  'key at (%.1f, %.1f, %.1f)'
                  % (ENEMY_WAKE_DISTANCE, key_at.x, key_at.y, key_at.z))

        if doom_music:
            doom_music.volume = DOOM_MUSIC_VOL
            if not doom_music.playing:
                doom_music.play()

        self.update_objective()
        flash_title(level['title'])
        fade_from_black(0.8)

        if level['voice_in_level']:
            invoke(self.play_in_level_voice, delay=4)

    # key, exit and pickups
    def place_key_and_exit(self):
        exit_index = self.level_index % len(EXIT_SPOTS)
        exit_spot = EXIT_SPOTS[exit_index]

        exit_yaw = (EXIT_SPOT_YAW[exit_index]
                    if exit_index < len(EXIT_SPOT_YAW) else 0)
        if self.level_index == 0:
            key_spot = KEY_SPOT_FIRST      # the easy one, first level only
        else:
            key_spot = KEY_SPOTS[(self.level_index - 1) % len(KEY_SPOTS)]

        def on_floor(p):
            return nearest_walkable(p, fallback=p)

        exit_spot = on_floor(exit_spot)
        key_spot = snap_to_doom_floor(key_spot, 'key')
        self.exit_door = ExitDoor(exit_spot, yaw=exit_yaw)
        # NO KEY ON THE SURVIVAL LEVEL.
        level = LEVELS[min(self.level_index, len(LEVELS) - 1)]
        self.key = KeyPickup(key_spot) if level['winnable'] else None
        self.exit_door_big = (ExitDoor(on_floor(EXIT_BIG_SPOT), EXIT_BIG_SIZE,
                                       yaw=EXIT_BIG_YAW)
                              if EXIT_BIG_ON else None)

        print('level: exit door %d facing %d degrees'
              % (exit_index + 1, exit_yaw))
        print(f'level: key at {tuple(round(v, 1) for v in key_spot)}, '
              f'exit at {tuple(round(v, 1) for v in exit_spot)}, '
              f'big exit at {tuple(round(v, 1) for v in EXIT_BIG_SPOT)}')

    def place_weapon_pickups(self, level):
        spots = walkable_spots()
        if not spots:
            return
        for spec in WEAPONS:
            if spec['key'] in weapons.owned:
                continue
            if spec['unlocked_at'] > self.level_index:
                continue
            fixed = spec.get('pickup_at')
            if fixed is not None:

                where = Vec3(fixed)
                g = floor_under(where)
                if g is not None and abs(g - where.y) <= 2.0:
                    where.y = g
                print('   %s pickup at your spot %s'
                      % (spec['name'], tuple(round(v, 1) for v in where)))
            else:
                options = [p for p in spots if 12 < distance(p, DOOM_SPAWN) < 60]
                if not options:
                    options = spots
                where = random.choice(options)
            self.pickups.append(WeaponPickup(spec, where))

    def place_health_packs(self, level):
        if not HEALTH_ON or HEALTH_PER_LEVEL <= 0:
            return
        spots = [p for p in walkable_spots()
                 if p.y < DOOM_SPAWN.y + ENEMY_MAX_HEIGHT
                 and math.hypot(p.x - DOOM_SPAWN.x,
                                p.z - DOOM_SPAWN.z) > HEALTH_MIN_FROM_SPAWN]
        if not spots:
            print('!! no walkable spots - no health packs placed')
            return
        chosen = spread_points(spots, HEALTH_PER_LEVEL, HEALTH_MIN_GAP)
        for p in chosen:
            self.health_packs.append(HealthPack(Vec3(p)))
        print('   DOOM: %d %s packs placed, %d health each, at least %.0fm apart'
              % (len(self.health_packs), HEALTH_LABEL.lower(), HEALTH_AMOUNT,
                 HEALTH_MIN_GAP))

    def fill_enemy_queue(self, level, count):
        tiers, weights = zip(*level['mix'].items()) if level['mix'] else (('weak',), (1,))
        total = float(sum(weights))
        self.enemy_queue = []
        for tier, w in zip(tiers, weights):
            self.enemy_queue.extend([tier] * max(1, int(round(count * w / total))))
        random.shuffle(self.enemy_queue)
        while len(self.enemy_queue) < count:
            self.enemy_queue.append(random.choice(tiers))
        return self.enemy_queue

    def next_tier(self, level):
        if not self.enemy_queue:
            self.fill_enemy_queue(level, 12)
        return self.enemy_queue.pop()

    def populate_level(self, level):
        per_room = level.get('per_room', ENEMY_PER_ROOM)
        corridors = level.get('corridors', ENEMY_IN_CORRIDORS)
        posts = enemy_posts(per_room, corridors)
        if not posts:
            print('!! no rooms found - falling back to spawning %d around you'
                  % level.get('alive', 20))
            self.fill_enemy_queue(level, level.get('alive', 20))
            for _ in range(level.get('alive', 20)):
                self.spawn_enemy(level)
            return
        self.fill_enemy_queue(level, len(posts))
        rooms = sum(1 for _p, kind in posts if kind == 'room')
        for spot, kind in posts:
            tier = self.next_tier(level)
            self.enemies.append(DoomEnemy(spot, tier, level['toughness'],
                                          post=spot, kind=kind))
        if level.get('boss'):
            invoke(self.spawn_boss, level, delay=6)
        counts = {}
        for e in self.enemies:
            counts[e.tier] = counts.get(e.tier, 0) + 1
        print('   DOOM: %d enemies posted - %d in rooms (%d each), %d in the '
              'corridors  [%s]'
              % (len(self.enemies), rooms, per_room, len(posts) - rooms,
                 ', '.join('%s x%d' % kv for kv in sorted(counts.items()))))

    def free_post(self, min_dist=14, max_dist=70):
        level = LEVELS[min(self.level_index, len(LEVELS) - 1)]
        posts = [p for p, _k in enemy_posts(
            level.get('per_room', ENEMY_PER_ROOM),
            level.get('corridors', ENEMY_IN_CORRIDORS))]
        here = player.world_position
        taken = [e.world_position for e in self.enemies if not e.dying]
        options = [p for p in posts
                   if min_dist < distance(p, here) < max_dist
                   and all(distance(p, t) > 2.5 for t in taken)]
        if options:
            return random.choice(options)
        return pick_spawn_point(player.position, min_dist=min_dist,
                                max_dist=max_dist)

    def take_key(self):
        self.has_key = True
        beep(pitch=4, length=0.25, wave='sine', volume=0.6)
        flash_title('KEY TAKEN  --  find the exit', 2.2)
        if self.exit_door:
            self.exit_door.unlock()
        if self.exit_door_big:
            self.exit_door_big.unlock()
        self.update_objective()

    def play_in_level_voice(self):
        if self.state != 'doom' or self.chapter in self.voices_played:
            return
        self.voices_played.add(self.chapter)
        voice.play(CHAPTERS[min(self.chapter, len(CHAPTERS) - 1)],
                   audio_name='voice_%d' % self.chapter, handler=True,
                   chapter=self.chapter)

    def spawn_enemy(self, level, tier=None, at=None):
        if tier is None:
            tier = self.next_tier(level)
        point = at if at is not None else self.free_post()
        e = DoomEnemy(point, tier, level['toughness'], post=point,
                      kind='corridor')
        self.enemies.append(e)
        return e

    def release_enemies(self):
        if self.enemies_released or self.state != 'doom':
            return
        self.enemies_released = True
        level = LEVELS[min(self.level_index, len(LEVELS) - 1)]
        self.populate_level(level)
        for e in self.enemies:
            e.wake(spread=False)
        flash_title(ENEMY_WAKE_MESSAGE, 2.2)
        clip = doom_sound('sight')
        if clip:
            clip.play()
        print('   DOOM: reached the key area - released %d enemies'
              % len(self.enemies))

    def spawn_boss(self, level):
        # snapped to the floor cannot arrive inside the geometry
        spot = snap_to_doom_floor(BOSS_SPAWN, 'boss')
        self.boss = DoomEnemy(spot, 'boss', level['toughness'], post=spot)
        # he uses the same sight and hearing rules as every other enemy now, which is jut so much easier
        self.enemies.append(self.boss)

    def enemy_died(self, enemy):
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        self.kills += 1
        # only your own kills count. something that walked into the acid is not a liver you took
        if getattr(enemy, 'killed_by_level', False):
            print('   liver: not counted, the sludge killed that one')
        else:
            # kills is per level, livers is for the whole run
            self.livers += 1
            refresh_livers()
        # THE BOSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS - killing him stops the game where it stands
        if enemy is self.boss and not self.boss_killed:
            self.boss_killed = True
            # three secondsish
            invoke(self.ending_ceo, delay=CEO_DEATH_DELAY)
        level = LEVELS[min(self.level_index, len(LEVELS) - 1)]
        # the garrison is fixed.
        if level['winnable']:
            return
        # except on the one that does not end
        for _ in range(2):
            if len(self.enemies) < level.get('alive', 60):
                self.spawn_enemy(level)
            else:
                break
        for e in self.enemies[-2:]:
            e.wake(spread=False)

    def update_objective(self):
        level = LEVELS[min(self.level_index, len(LEVELS) - 1)]
        if not level['winnable']:
            left = max(0.0, level.get('survive', SURVIVE_SECONDS) - self.doom_timer)
            if self.survived:
                objective_text.text = 'GET OUT'
                objective_text.color = RGB(120, 235, 140)
            else:
                objective_text.text = '%s   %d' % (SURVIVE_OBJECTIVE, int(left) + 1)
                objective_text.color = RGB(255, 150, 60)
        elif not self.has_key:
            objective_text.text = 'FIND THE KEY'
            objective_text.color = RGB(255, 110, 110)
        else:
            objective_text.text = 'REACH THE EXIT'
            objective_text.color = RGB(120, 235, 140)

    # walking out of the office
    def update_wandering(self):
        # how far OUTSIDE the office rectangle are you. negative means inside
        dx = abs(player.x - office_root.x) - OFFICE_BOX_HALF.x
        dz = abs(player.z - office_root.z) - OFFICE_BOX_HALF.y
        outside_by = max(dx, dz)
        raw = 1.0 - clamp(outside_by / OFFICE_BOX_FADE, 0, 1)

        # smoothstep, not a straight ramp, weird calculation here
        raw = raw * raw * (3.0 - 2.0 * raw)

        self.office_pull = lerp(self.office_pull, raw,
                                min(1, time.dt * OFFICE_FADE_SPEED))

        outside = self.office_pull < 0.5
        if outside != self.outside_now:
            self.outside_now = outside
            if outside:
                show_prompt('')

        # the village has no weather at all now, no fadeee
        set_scene_fog(False)

        if OFFICE_SLOWS_YOU:
            movement.set_base_speed(lerp(WORLD_SPEED, OFFICE_SPEED,
                                         self.office_pull))
        else:
            movement.set_base_speed(WORLD_SPEED)


    # the compass at the top of the screen, super nice i should add another one for gneeral objectives in village
    def compass_target(self):
        if self.state != 'doom':
            return None
        if not self.has_key and self.key:
            return self.key.world_position
        if self.has_key and self.exit_door:
            return self.exit_door.world_position
        return None

    def update_compass(self):
        target = self.compass_target()
        showing = target is not None
        compass_line.enabled = showing
        compass_marker.enabled = showing
        compass_distance.enabled = showing
        if not showing:
            return

        to_target = target - player.world_position
        bearing = math.degrees(math.atan2(to_target.x, to_target.z)) - player.rotation_y
        bearing = (bearing + 180) % 360 - 180          # wrap to -180..180

        offset = clamp(bearing / COMPASS_FOV, -1, 1) * (COMPASS_WIDTH / 2)
        compass_marker.x = lerp(compass_marker.x, offset, min(1, time.dt * 12))
        behind = abs(bearing) > COMPASS_FOV
        compass_marker.color = (RGB(190, 160, 80, 130) if behind
                                else (RGB(120, 235, 140) if self.has_key
                                      else RGB(255, 120, 120)))
        compass_distance.text = f'{int(to_target.length())}m'
        compass_distance.color = RGB(190, 175, 130, 150 if behind else 220)

    def finish_level(self):
        self.state = 'transition'
        self.kill_all_enemies()
        voice.stop()
        show_prompt('')
        flash_title('CLEARED', 2.0)
        self.chapter += 1
        self.level_index += 1

        if self.level_index >= len(LEVELS):
            fade_to_black(1.4, then=self.enter_finale)
        elif LEVELS[self.level_index]['voice_in_level']:
            fade_to_black(1.4, then=self.enter_doom)      # no going back now
        else:
            # home, not the village. the phone is ringing again by the time you stand in it
            # not in the game anymore was a veeeery old feature of fade into the office which isnt there naymore
            fade_to_black(1.4, then=self.enter_apartment)

    def player_died(self):
        if death_screen.showing:
            return
        level = LEVELS[min(self.level_index, len(LEVELS) - 1)]
        self.state = 'transition'
        self.kill_all_enemies()
        voice.stop()
        self.stop_ring()
        show_prompt('')
        scripted = not level['winnable']
        if scripted and DEATH_STORY_DEATH_CONTINUES:
            death_screen.show(then=lambda: fade_to_black(0.8,
                                                         then=self.enter_finale),
                              hint='[E]  or click')
        elif DEATH_RETURNS_TO == 'retry':
            death_screen.show(then=lambda: fade_to_black(0.8,
                                                         then=self.enter_doom))
        else:
            death_screen.show(then=self._back_to_menu)


    # FINALE
    def mark_campaign_done(self, how):
        if not self.campaign_done:
            self.campaign_done = True
            print('campaign complete (%s) - door 5 is unlocked' % how)
            invoke(flash_notice, 'the last door on the street is open now.',
                   7.0, delay=2.0)

    def enter_finale(self):
        self.mark_campaign_done('reached the finale')
        self.clear_scenes()
        # no phone ringing here
        self.phone_ringing = False
        self.stop_ring()
        self.state = 'finale'
        apartment_root.enabled = True
        office_root.enabled = True
        city_root.enabled = False
        friend.enabled = True
        door_to_doom.enabled = False
        door_glow.enabled = False
        door_label.enabled = False

        # The finale is the office again, so it keeps its fog, whatever imaginary fog it isnt even there
        set_scene_fog(True, color.black, FOG_FINALE)
        set_clip('finale')

        movement.set_eye_height('finale')
        player.speed = OFFICE_SPEED
        place_player(APARTMENT_AT + APARTMENT_SPAWN)
        player.rotation_y = 0
        player.camera_pivot.rotation_x = 0
        player.health = PLAYER_MAX_HP
        player.holding = 'gun'
        show_viewmodel('gun')
        crosshair.enabled = True

        self.finale_choice_ready = False
        self.ending_running = False
        fade_from_black(2.0)
        invoke(self.finale_speech, delay=1.5)

    def finale_speech(self):
        #conversation based on whta the player did
        lines = FINALE_LINES_PACIFIST if self.livers == 0 else FINALE_LINES
        if self.livers == 0:
            print('   FINALE: zero livers - the pacifist route is open')
        # 6handler is the pacifist version, 7handler the normal one
        voice.play(lines, on_finish=self.offer_choices, caller='',
                   finale='pacifist' if self.livers == 0 else 'normal')

    def offer_choices(self):
        self.finale_choice_ready = True
        # the box should say the options
        flash_notice('shoot him and the money is yours - or walk out and he '
                     'keeps it', 6.0)
        exit_door.enabled = FINALE_EXTRA_DOOR
        exit_label.enabled = FINALE_EXTRA_DOOR
        exit_label.text = 'EXIT'
        apartment_door_inside.enabled = True
        show_prompt('[LMB] shoot him   /   [E] on your own front door to leave')

    # ENDINGS
    def ending_kill(self):
        if self.ending_running:
            return
        self.ending_running = True
        self.mark_campaign_done('shot him')
        self.finale_choice_ready = False
        show_prompt('')
        stop_all_voice_clips() # its just the character head saying something in the text box

        show_ending_card()
        friend.animate('alpha', 0, duration=1.2)
        invoke(setattr, friend, 'enabled', False, delay=1.3)
        # shooting him is the winning path in this case
        talk_box.start(ENDING_KILL, '', voice_clip=None,
                       on_finish=self.go_and_buy_it)

    def go_and_buy_it(self):
        # (mark_campaign_done already ran in ending_kill)
        self.bought_house = True
        self.door_open = False          # no more DOOM levels
        self.ending_running = False
        self.finale_choice_ready = False
        fade_to_black(1.4, then=self.enter_office)
        invoke(flash_notice,
               'the for sale sign is down. door 5 is yours - go and see it.',
               9.0, delay=2.4)

    def ending_leave(self):
        if self.ending_running:
            return
        self.ending_running = True
        self.mark_campaign_done('walked out')
        self.finale_choice_ready = False
        show_prompt('')
        if self.livers == 0:
            self.pacifist_offer = True
            voice.play(ENDING_LEAVE_PACIFIST,
                       on_finish=self._back_to_village_clean, caller='')
        else:
            self.credits_after_thanks = True
            stop_all_voice_clips()
            talk_box.start(ENDING_LEAVE, '', voice_clip=None,
                           on_finish=thanks_card_after)

    def _back_to_village_clean(self):
        self.ending_running = False
        self.finale_choice_ready = False
        self.door_open = False
        fade_to_black(1.2, then=self.enter_office)
        invoke(flash_notice, 'go and find the scientist. door 2.', 6.0, delay=2.2)

    def talk_finished(self, speaker):
# dj signs  the lease metphorically and door 5 becomes the throne room
        if (self.bought_house and not self.lease_from_dj
                and getattr(speaker, 'npc_room', None) == 3):
            self.lease_from_dj = True
            beep(pitch=8, length=0.4, wave='sine', volume=0.5)
            flash_notice('the lease is signed. door 5 is yours.', 8.0)
            print('   the DJ signed - door 5 now opens on the throne room')
        if (self.pacifist_offer and not self.lease_signed
                and getattr(speaker, 'npc_room', None) == 0):
            self.lease_signed = True
            beep(pitch=8, length=0.4, wave='sine', volume=0.5)
            flash_notice('the lease is sealed.', 6.0)
            print('   the scientist signed - teleporting to the house')
            invoke(self.ending_owned, delay=2.0)

    def sign_the_lease(self):
        self.signed = True
        # THE THANKS CARD - the walk-out ending finishes here too.
        talk_box.start(ENDING_LEASE, 'THE DJ', on_finish=thanks_card_after)

        if not ENDING_EXPLORE:
            invoke(self.roll_credits, delay=2.0 + 3.0 * len(ENDING_LEASE))

    def _go_garden(self, then_sign=True, happy=False):
        self.clear_scenes()
        self.happy_ending = bool(happy)
        self.state = 'ending'
        garden_root.enabled = True
        set_sky_texture(SKY_TEXTURE_HAPPY if self.happy_ending
                        else SKY_TEXTURE_DEFAULT)
        sky.enabled = True
        set_scene_fog(False)
        set_clip('ending')
        movement.set_eye_height('ending')
        player.speed = 6
        if plot_exit_door is not None:
            plot_exit_door.enabled = True     # the way back out
        place_player(ROOM_PLOT_SPAWN)
        player.rotation_y = ROOM_PLOT_FACE
        player.holding = 'hand'
        show_viewmodel('hand')
        fade_from_black(2.5)
        if then_sign:
            invoke(self.sign_the_lease, delay=2.5)


    def ending_ceo(self):
        if self.ending_running:
            return
        self.ending_running = True
        self.boss_killed = True        #  the demonENDING trophy must be added
        self.mark_campaign_done('killed the CEO')
        self.state = 'transition'
        self.kill_all_enemies()
        voice.stop()
        clear_all_ads()
        show_prompt('')
        set_hud(False)
        crosshair.enabled = False
        if hands_rig:
            hands_rig.enabled = False
        if gun_hands:
            gun_hands.enabled = False
        if weapons:
            weapons.show(False)
        if doom_music and doom_music.playing:
            doom_music.stop()
        # stop being able to walk but the game is NOT paused, the box types itself out on its update
        player.enabled = False
        mouse.locked = False
        fade_to_black(CEO_FADE_TIME, then=self._ceo_show)

    def _ceo_show(self):
        fade.alpha = 0
        ceo_screen.then = self._ceo_done
        ceo_screen.show()
        # no timer on this - offer_button fires when the LAST box has been read
        # this ending runs on the voice notes clock, not yours. the fade is scheduled off the clips own length
        talk_box.start(ENDING_CEO, 'THE CEO OF THE UNIVERSE',
                       voice_clip=BOSS_ENDING_VOICE, voice_loop=False,
                       on_finish=lambda: (ceo_screen.offer_button(),
                                          thanks_card_after()))
        self.wait_for_boss_voice()

    def wait_for_boss_voice(self):
        clip = load_voice(BOSS_ENDING_VOICE)
        seconds = clip.length if clip is not None else 0.0
        if seconds <= 0.1:
            seconds = BOSS_ENDING_FALLBACK
            print('!! %s: no length from panda3d, so the boss ending will run '
                  'for %.0fs' % (BOSS_ENDING_VOICE, seconds))
        else:
            print('   boss ending: holding for %.1fs while the voice note '
                  'plays out' % seconds)
        invoke(self._boss_voice_done, delay=seconds + BOSS_ENDING_TAIL)

    def _boss_voice_done(self):
        if self.state != 'transition':
            return               # you already clicked the button. Leave it.
        stop_all_voice_clips()
        fade_to_black(2.0, then=self._ceo_done)

    def _ceo_black(self):
        talk_box.close()
        ceo_screen.go_black()
        ceo_screen.offer_button()

    def _ceo_done(self):
        talk_box.close()
        ceo_screen.hide()
        self.ending_running = False
        self._back_to_menu()

    def roll_credits(self):
        self.state = 'ending'
        show_prompt('')
        fade_to_black(2.5, then=self._back_to_menu)

    def _back_to_menu(self):
        self.clear_scenes()
        self.state = 'menu'
        # the thanks card does not follow to the  title screen, any key clears it
        thanks_card.enabled = False
        self.credits_after_thanks = False
        friend.enabled = True
        friend.alpha = 1
        _set_menu(True)
        fade.alpha = 0

    # per-frame
    def update(self):
        # this runs BEFORE the menu check, or fog set in the village rides through the menu into the next scene
        if self.state not in FOG_SCENES and fog_is_on():
            set_scene_fog(False)

        if _menu_open:
            return
        if self.state == 'office':
            self.update_wandering()

        # the iphone alarm is the ring now, and it gets quieter as you walk away from the desk, this barely works due to the size of the apartment
        if self.phone_ringing:
            self.ring_timer += time.dt
            pulse = (math.sin(time.time() * 6) + 1) / 2
            # tint runs from the resting dim up to full white so the texture stays readable
            lit = 120 + pulse * 135 * self.office_pull
            phone.color = RGB(lit, lit * 0.96, lit * 0.98)
            ring = _sound_cache.get(RING_SOUND)
            if ring is not None:
                ring.volume = (RING_VOLUME * (0.10 + 0.90 * self.office_pull)
                               if RING_FADE_WITH_DISTANCE else RING_VOLUME)
                if RING_LOOP:
                    if not ring.playing:
                        ring.play(restart=False)
                elif self.ring_timer > 3.0:
                    self.ring_timer = 0
                    ring.play()
            else:
                # no alarm file, then just beeps from ursina engine local, if it wouldnt load
                interval = 2.0 + (1 - self.office_pull) * 2.5
                if self.ring_timer > interval:
                    self.ring_timer = 0
                    vol = 0.35 * self.office_pull
                    if vol > 0.02:
                        beep(pitch=-2, length=0.18, wave='sine', volume=vol)
                        invoke(beep, -2, 0.18, 'sine', vol, delay=0.22)

        # the red door is E only too, see go_to_doom()
        if DOOR_WALK_IN and self.state == 'office' and self.door_open:
            if distance(player.world_position, door_to_doom.world_position) < 2.5:
                self.go_to_doom()

        if self.house_grace > 0:
            self.house_grace -= time.dt

        # every door is E only now. walking into them kept grabbing me when i meant to walk past. DOOR_WALK_IN brings it back, but i dont use it once again
        if DOOR_WALK_IN and self.state == 'office' and self.house_grace <= 0:
            for house in village_houses:
                d = house['door']
                gap = Vec3(player.world_position - d.world_position)
                if Vec2(gap.x, gap.z).length() < HOUSE_WALK_IN_RANGE \
                        and abs(gap.y) < 2.2:
                    self.enter_house(house['room'])
                    break
        if (self.state == 'doom' and ENEMY_HOLD_UNTIL_KEY
                and not self.enemies_released):
            target = self.key.world_position if self.key else None
            if target is not None:
                gap = math.hypot(player.x - target.x, player.z - target.z)
                if gap < ENEMY_WAKE_DISTANCE:
                    self.release_enemies()
            else:
                self.release_enemies()      # no key on this level: just survive

        # the old press-a-key-to-start gate is gone. standing completely still used to make you untouchable, annoying.
        # the level that will not end
        if self.state == 'doom':
            level = LEVELS[min(self.level_index, len(LEVELS) - 1)]
            self.update_compass()

            if not level['winnable']:
                # survive it, do not die in it. the clock opens the way out
                self.doom_timer += time.dt
                self.update_objective()
                if (not self.survived
                        and self.doom_timer >= level.get('survive',
                                                         SURVIVE_SECONDS)):
                    self.survived = True
                    self.has_key = True   # so the doors open when palyer has key
                    if self.exit_door:   # and the compass has something to aim at
                        self.exit_door.unlock()
                    if self.exit_door_big:
                        self.exit_door_big.unlock()
                    flash_title(SURVIVE_MESSAGE, 3.0)
                    flash_notice(SURVIVE_MESSAGE)
                    clip = doom_sound('door')
                    if clip:
                        clip.play()
                    self.update_objective()


            # fell out of the world - straight back to the levels own start, silently, suuuuper nice feature.
            if player.y < -30:
                # snapped, or falling out would put you back on the ceiling
                place_player(snap_to_doom_floor(DOOM_SPAWN, 'respawn'))
                player.rotation_y = 0
                player.camera_pivot.rotation_x = 0

        # the finale exit is E only as well now
        if (DOOR_WALK_IN and self.state == 'finale'
                and self.finale_choice_ready
                and distance(player.world_position, exit_door.world_position) < 2.5):
            self.ending_leave()


game = Game()




# OUT OF BOUNDS
_doom_extent = None


def doom_extent():
    global _doom_extent
    if _doom_extent is not None or doom_collision is None:
        return _doom_extent
    try:
        v = doom_collision.model.vertices
        _doom_extent = (min(p[0] for p in v), max(p[0] for p in v),
                        min(p[1] for p in v), max(p[1] for p in v),
                        min(p[2] for p in v), max(p[2] for p in v))
    except Exception:
        _doom_extent = None
    return _doom_extent


class FallGuard(Entity):
    def __init__(self):
        super().__init__()
        self.tick = 0.0
        self.cool = 0.0
        self.saves = 0
        self.in_a_row = 0
        self.last_scene = None
        self.given_up = False

    def update(self):
        if not FALL_GUARD_ON or game is None or _menu_open or GODMODE:
            return
        if not player.enabled or _last_spawn[0] is None:
            return
        if game.state in ('menu', 'transition'):
            return
        if getattr(player_settler, 'frames_left', 0) > 0:
            return
        if self.last_scene != game.state:
            self.last_scene = game.state       # a new scene, a clean slate
            self.in_a_row = 0
            self.given_up = False
        self.cool -= time.dt
        self.tick -= time.dt
        if self.tick > 0 or self.cool > 0 or self.given_up:
            return
        self.tick = FALL_GUARD_TICK
        floor = _last_spawn[0].y
        if player.y >= floor - FALL_LIMIT:
            self.in_a_row = 0
            return

        self.saves += 1
        self.in_a_row += 1
        self.cool = FALL_GUARD_COOLDOWN
        if self.in_a_row >= FALL_GUARD_GIVE_UP:
            self.given_up = True
            print('!! fall guard: %d rescues in a row in scene %r - that room '
                  'has no floor under (%.1f, %.1f), not a stray jump. Giving '
                  'up rather than holding you in place; walk to a door.'
                  % (self.in_a_row, game.state, _last_spawn[0].x,
                     _last_spawn[0].z))
            flash_notice('beep boop code error sorry', 5.0)
            return

        print('   fall guard: caught you at y=%.1f (%.1fm under the spawn) in '
              'scene %r - put back. Save #%d this session.'
              % (player.y, floor - player.y, game.state, self.saves))
        place_player(Vec3(_last_spawn[0]) + Vec3(0, 1.0, 0), settle=False)
        try:
            player.velocity = 0
            player.grounded = False
        except Exception:
            pass
        flash_notice(random.choice(FALL_MESSAGES), 4.0)


fall_guard = FallGuard()



# MOVING IN PIECES ON A SLOW FRAME
_real_player_update = player.update


def substepped_player_update():
    if not MOVE_SUBSTEP_ON:
        _real_player_update()
        return

    frame_dt = time.dt

    # how far this frame is going to move us, at the worst
    speed = getattr(player, 'speed', 5.0)
    would_move = speed * frame_dt

    # how many checks that needs
    steps = 1
    if would_move > MOVE_SUBSTEP_MAX:
        steps = int(math.ceil(would_move / MOVE_SUBSTEP_MAX))
    if steps > MOVE_SUBSTEP_CAP:
        steps = MOVE_SUBSTEP_CAP
    if steps < 1:
        steps = 1

    if steps == 1:
        _real_player_update()          # a normal frame. Nothing changes.
        return

    # a slow frame. Walk it in pieces, checking the walls at every piece.
    time.dt = frame_dt / steps
    try:
        for _ in range(steps):
            _real_player_update()
    finally:
        time.dt = frame_dt             # always put it back, even on an error


player.update = substepped_player_update


# the controller refuses to move you at all if either of its rays hits something, it does not slide you along the wall
# this is actaully pretty bad for speedrunners, but more on that in the importnat notes.md or whatever i call it later
class UnstickHelper(Entity):
    def __init__(self):
        super().__init__()
        self.stuck_for = 0.0
        self.was_at = None
        self.came_from = None
        self.rescues = 0
#main movement
    def wants_to_move(self):
        if held_keys['w']:
            return True
        if held_keys['a']:
            return True
        if held_keys['s']:
            return True
        if held_keys['d']:
            return True
        return False

    def update(self):
        if not UNSTICK_ON:
            return
        if game is None or _menu_open or _paused_menu:
            return
        if not player.enabled or player.busy:
            return
        if talk_box.open or dialogue_cam_on:
            return

        here = Vec3(player.world_position)

        if self.was_at is None:
            self.was_at = here
            return

        moved = distance(here, self.was_at)

        # remember somewhere open to be pushed back towards
        if moved > 0.25:
            self.came_from = self.was_at

        if not self.wants_to_move():
            self.stuck_for = 0.0
            self.was_at = here
            return

        if moved > UNSTICK_DISTANCE:
            self.stuck_for = 0.0
            self.was_at = here
            return

        # holding a key, going nowhere
        self.stuck_for += time.dt
        if self.stuck_for < UNSTICK_SECONDS:
            return

        self.free_the_player(here)
        self.stuck_for = 0.0
        self.was_at = Vec3(player.world_position)

    def free_the_player(self, here):
        self.rescues += 1
        goal = here + Vec3(0, UNSTICK_LIFT, 0)

        if self.came_from is not None:
            back = self.came_from - here
            back.y = 0
            if back.length() > 0.05:
                back = back.normalized() * UNSTICK_PUSH
                goal = goal + back

        player.position = goal
        try:
            player.velocity = 0
        except Exception:
            pass
        print('   unstick: you were wedged at (%.1f, %.1f, %.1f) in scene %r ' # this is like one of the failsafes AI made and i think its like implossibel this will ever trigger
              '- nudged out. Rescue #%d this session.'
              % (here.x, here.y, here.z, game.state, self.rescues))


unstick_helper = UnstickHelper()


class OutOfBounds(Entity):
    def __init__(self):
        super().__init__()
        self.tick = 0.0
        self.cool = 0.0

    def update(self):
        if not OOB_ON or game is None or _menu_open:
            return
        self.cool -= time.dt
        self.tick -= time.dt
        if self.tick > 0:
            return
        self.tick = OOB_TICK
        if self.cool > 0:
            return
        p = player.world_position
        out = False
        if game.state == 'office' and village_bounds:
            x0, x1, z0, z1 = village_bounds
            out = (p.x < x0 - OOB_MARGIN or p.x > x1 + OOB_MARGIN
                   or p.z < z0 - OOB_MARGIN or p.z > z1 + OOB_MARGIN)
        elif game.state == 'doom':
            box = doom_extent()
            if box:
                out = (p.x < box[0] - 6 or p.x > box[1] + 6
                       or p.z < box[4] - 6 or p.z > box[5] + 6
                       or p.y < box[2] - 12)
        elif game.state == 'house':
            out = p.y < ROOM_BASE.y - 20
        elif game.state == 'ending':
            out = abs(p.x - GARDEN_OFFSET.x) > 120
        if not out:
            return
        self.cool = OOB_REPEAT
        flash_notice(OOB_MESSAGE)
        self.bring_them_back(p)

    def bring_them_back(self, p):
        if not OOB_RETURN_YOU:
            return
        if _last_spawn[0] is None:
            return
        print('   out of bounds: you were at (%.1f, %.1f, %.1f) in scene %r '
              '- put back on the last safe spot.' % (p.x, p.y, p.z, game.state))
        place_player(Vec3(_last_spawn[0]) + Vec3(0, 1.0, 0), settle=False)
        try:
            player.velocity = 0
            player.grounded = False
        except Exception:
            pass


out_of_bounds = OutOfBounds()



# INTERACTION - what E does basically
SPAWN_CLEARANCE    = 0.12
# how far the floor ray may disagree with the spawn point before it is ignored
SPAWN_FLOOR_TOLERANCE = 3.0
# how far above the spawn a surface may be and still count as floor.
SPAWN_FLOOR_RISE      = 3.0
# where place_player last put you, for FallGuard
_last_spawn = [None]
DOOR_ENTRY_LIFT    = 1.0    # only the FALLBACK now, when no floor is found
SETTLE_FRAMES      = 45     # frames the safety net stays armed (~0.75s) roughly 45 frames, to be fair it depends on the computer and framerate
SETTLE_RESCUE_DROP = 1.5   # metres BELOW the spawn that counts as fell through. must be more than DOOR_ENTRY_LIFT


class DoomBoundsGuard(Entity):
    def update(self):
        if game is None or game.state != 'doom' or doom_play_area is None:
            return
        if not player.enabled or GODMODE:
            return
        x0, x1, z0, z1, ceiling = doom_play_area
        px, pz = player.x, player.z
        out = False
        if px < x0:
            player.x = x0 + DOOM_PUSH_BACK; out = True
        elif px > x1:
            player.x = x1 - DOOM_PUSH_BACK; out = True
        if pz < z0:
            player.z = z0 + DOOM_PUSH_BACK; out = True
        elif pz > z1:
            player.z = z1 - DOOM_PUSH_BACK; out = True
        # over the top of the level - only possible by clipping, so drop them
        if player.y > ceiling + 8.0:
            player.y = ceiling
            out = True
        if out:
            try:
                player.velocity = 0
            except Exception:
                pass
            # put them on the floor of wherever they have been pushed to
            g = floor_under(player.position)
            if g is not None:
                player.y = g + SPAWN_CLEARANCE
            flash_title('GET BACK IN', 0.8)


doom_bounds_guard = DoomBoundsGuard()


class PlayerSettler(Entity):
    def __init__(self):
        super().__init__()
        self.frames_left = 0
        self.hold_at = None
        self.floor_y = 0.0

    def hold(self, pos, floor_y):
        self.hold_at = Vec3(pos)         # where to put you back (already lifted)
        self.floor_y = floor_y           # the spawn itself, i.e. the floor
        self.frames_left = SETTLE_FRAMES

    def cancel(self):
        self.frames_left = 0
        self.hold_at = None

    def update(self):
        if self.frames_left <= 0 or self.hold_at is None:
            return
        self.frames_left -= 1

        # it only catches a real fall-through, not the landing. the drop from DOOR_ENTRY_LIFT is the POINT
        if player.y < self.floor_y - SETTLE_RESCUE_DROP:
            print('   (caught a fall-through at y=%.2f, putting you back on '
                  'the spawn)' % player.y)
            player.position = Vec3(self.hold_at)
            try:
                player.velocity = 0
            except Exception:
                pass
        if self.frames_left <= 0:
            self.hold_at = None
player_settler = PlayerSettler()



def floor_under(pos, up=4.0, down=30.0):
    try:
        ignore = tuple([player] + list(no_climb_boxes) + list(doom_bounds_boxes))
    except Exception:
        ignore = (player,)
    surfaces = []
    y = pos.y + up
    for _ in range(8):
        try:
            hit = raycast(Vec3(pos.x, y, pos.z), Vec3(0, -1, 0),
                          distance=(y - (pos.y - down)), ignore=ignore)
        except Exception:
            break
        if not hit.hit:
            break
        surfaces.append(hit.world_point.y)
        y = hit.world_point.y - 0.05          # carry on under it
        if y < pos.y - down:
            break
    if not surfaces:
        return None
    return min(surfaces, key=lambda h: abs(h - pos.y))


def place_player(pos, lift=None, face=None, settle=True):
    if lift is None:
        lift = DOOR_ENTRY_LIFT
    pos = Vec3(pos)

    ground = floor_under(pos)

    # only trust a floor near the spawn. place_player runs on the same frame the new scene switches on, and the ray can miss and hit a lower storey instead
    if ground is not None and -SPAWN_FLOOR_TOLERANCE <= (ground - pos.y) <= SPAWN_FLOOR_RISE:
        where = Vec3(pos.x, ground + SPAWN_CLEARANCE, pos.z)
    elif ground is not None:
        where = Vec3(pos.x, pos.y + SPAWN_CLEARANCE, pos.z)
        print('   (floor ray said y=%.2f but the spawn says %.2f - too far '
              'apart to trust, using the spawn)' % (ground, pos.y))
    else:
        where = Vec3(pos.x, pos.y + SPAWN_CLEARANCE, pos.z)
        print('   (no floor collider under the spawn %s yet - using the spawn '
              'height and watching for a fall)'
              % tuple(round(v, 1) for v in pos))
    try:
        head = raycast(where + Vec3(0, 0.05, 0), Vec3(0, 1, 0),
                       distance=movement.eye + 0.2,
                       ignore=tuple([player] + list(no_climb_boxes)))
        if head.hit and head.distance < movement.eye * 0.6:
            print('   (something solid %.2fm over the spawn - nudging you '
                  'clear of it)' % head.distance)
            where.y = max(where.y - (movement.eye - head.distance), (ground or where.y))
    except Exception:
        pass

    # every scene change comes through here, and FallGuard reads it
    _last_spawn[0] = Vec3(where)
    player.position = where
    if face is not None:
        player.rotation_y = face
    player.camera_pivot.rotation_x = 0
    # stop whatever fall was in progress, or you keep last scene's speed
    try:
        player.velocity = 0
    except Exception:
        pass
    if settle:
        player_settler.hold(where, Vec3(pos).y)
    return where


def look_target():
    ignore = [player] + no_climb_boxes
    hit = raycast(camera.world_position, camera.forward,
                  distance=INTERACT_RANGE, ignore=ignore)
    return hit.entity if hit.hit else None


def phone_in_reach():
    if game is None or game.state not in ('apartment', 'office', 'finale'):
        return False
    if not office_root.enabled:
        return False
    at = phone.world_position
    to = at - player.world_position
    if to.length() > PHONE_REACH_RANGE:
        return False
    fwd = camera.forward
    d = to.normalized()
    return (d.x * fwd.x + d.y * fwd.y + d.z * fwd.z) > 0.35

# Everything the camera needs to remember while it is away from your head.
dialogue_cam_on = False        # is it up right now?
dialogue_cam_npc = None        # who we are looking at
dialogue_cam_home_pos = None   # where your head was, in world coordinates
dialogue_cam_home_rot = None   # and which way it was pointing
dialogue_cam_home_fov = GAMEPLAY_FOV   # and how wide the lens was
# true from the start of a conversation until the camera is home and the cooldown is done. this is the flag that stopped the zoom sticking
dialogue_cam_busy = False


def npc_focus_point(npc):
    up = NPC_TARGET_HEIGHT * DIALOGUE_CAM_LOOK_AT
    return npc.world_position + Vec3(0, up, 0)


def npc_camera_spot(npc, focus):
    away = player.world_position - npc.world_position
    away.y = 0
    if away.length() < 0.05:
        # you are standing exactly on top of them. pick a direction rather than dividing by zero
        away = Vec3(0, 0, 1)
    away = away.normalized()

    side = Vec3(-away.z, 0, away.x)
    spot = focus + away * DIALOGUE_CAM_DISTANCE
    spot = spot + side * DIALOGUE_CAM_SIDE
    spot = spot + Vec3(0, DIALOGUE_CAM_LIFT, 0)
    return spot


def rotation_looking_at(from_pos, to_pos):
    keep_pos = camera.position
    keep_rot = camera.rotation
    camera.position = from_pos
    camera.look_at(to_pos)
    answer = camera.rotation
    camera.position = keep_pos
    camera.rotation = keep_rot
    return Vec3(answer[0], answer[1], answer[2])


def shortest_turn(from_angle, to_angle):
    difference = (to_angle - from_angle) % 360.0
    if difference > 180.0:
        difference = difference - 360.0
    return from_angle + difference


def nearest_rotation(from_rot, to_rot):
    return Vec3(shortest_turn(from_rot[0], to_rot[0]),
                shortest_turn(from_rot[1], to_rot[1]),
                shortest_turn(from_rot[2], to_rot[2]))


def turn_npc_to_camera(npc, spot):
    if not DIALOGUE_CAM_TURN_NPC:
        return
    to_camera = Vec3(spot) - npc.world_position
    to_camera.y = 0
    if to_camera.length() < 0.05:
        return
    npc.rotation_y = math.degrees(math.atan2(to_camera.x, to_camera.z))


def begin_dialogue_camera(npc):
    global dialogue_cam_on, dialogue_cam_npc, dialogue_cam_busy
    global dialogue_cam_home_pos, dialogue_cam_home_rot, dialogue_cam_home_fov
    if not DIALOGUE_CAM_ON:
        return
    if dialogue_cam_on:
        return
    if npc is None:
        return
    # THE COOLDOWN, and this is the fix for the stuck zoom. E the instant a box closed used to save where the camera was from halfway through the last glide
    if dialogue_cam_busy:
        return

    dialogue_cam_busy = True

    #remember where your head was, so we can put it back exactly
    dialogue_cam_home_pos = Vec3(camera.world_position)
    dialogue_cam_home_rot = Vec3(camera.world_rotation[0],
                                 camera.world_rotation[1],
                                 camera.world_rotation[2])
    # NOT camera.fov. a constant, so it cannot be read mid-animation
    dialogue_cam_home_fov = GAMEPLAY_FOV

    # work out the shot before letting go of the player, npc_camera_spot() asks where you are standing
    focus = npc_focus_point(npc)
    spot = npc_camera_spot(npc, focus)

    # let go. the freeze, the cursor and the free camera are all one flag
    player.enabled = False

    # the camera is parented to the scene now, so position IS world position
    target_rot = rotation_looking_at(spot, focus)
    target_rot = nearest_rotation(camera.rotation, target_rot)
    camera.animate_position(spot, duration=DIALOGUE_CAM_MOVE_TIME,
                            curve=curve.in_out_quad)
    camera.animate_rotation(target_rot, duration=DIALOGUE_CAM_MOVE_TIME,
                            curve=curve.in_out_quad)
    camera.animate('fov', DIALOGUE_CAM_FOV, duration=DIALOGUE_CAM_MOVE_TIME,
                   curve=curve.in_out_quad)
#look at the lens
    turn_npc_to_camera(npc, spot)

    #nothing of yours belongs in a portrait like hands and feet
    hide_hands_for_dialogue()

    dialogue_cam_npc = npc
    dialogue_cam_on = True


def hide_hands_for_dialogue():
    crosshair.enabled = False
    viewmodel.enabled = False
    if hands_rig:
        hands_rig.enabled = False
    if gun_hands:
        gun_hands.enabled = False
    if weapons:
        weapons.show(False)
    if player_body:
        player_body.enabled = False


def end_dialogue_camera(snap=False):
    global dialogue_cam_on, dialogue_cam_npc, dialogue_cam_busy
    if not dialogue_cam_on:
        # a scene change still has to clear the busy flag, or E refuses to work for the rest of the game
        if snap:
            dialogue_cam_busy = False
            camera.fov = GAMEPLAY_FOV
        return
    dialogue_cam_on = False
    npc, dialogue_cam_npc = dialogue_cam_npc, None

    if snap or dialogue_cam_home_pos is None:
        finish_dialogue_camera()
        return

    # glide back to exactly where your head was, then hand it over
    home_rot = nearest_rotation(camera.rotation, dialogue_cam_home_rot)
    camera.animate_position(dialogue_cam_home_pos,
                            duration=DIALOGUE_CAM_MOVE_TIME,
                            curve=curve.in_out_quad)
    camera.animate_rotation(home_rot, duration=DIALOGUE_CAM_MOVE_TIME,
                            curve=curve.in_out_quad)
    camera.animate('fov', dialogue_cam_home_fov,
                   duration=DIALOGUE_CAM_MOVE_TIME, curve=curve.in_out_quad)
    invoke(finish_dialogue_camera, delay=DIALOGUE_CAM_MOVE_TIME + 0.02)


def finish_dialogue_camera():
    if dialogue_cam_on:
        return                 # another conversation started mid-glide
    # ALWAYS the gameplay FOV. there is no path through here that leaves you zoomed in
    camera.fov = GAMEPLAY_FOV
    # the cooldown starts now, measured from the camera actually being back on your head
    invoke(release_dialogue_camera, delay=DIALOGUE_CAM_COOLDOWN)
    # do not hand the controls back if you died or an ending started during the glide
    if game is not None and game.state in ('menu', 'transition'):
        return
    if _menu_open or _paused_menu:
        return
    player.enabled = True
    if game is not None:
        show_viewmodel(player.holding)
    crosshair.enabled = True
    if player_body:
        player_body.enabled = SHOW_BODY


def release_dialogue_camera():
    global dialogue_cam_busy
    if dialogue_cam_on:
        return                 # a new conversation began during the cooldown
    dialogue_cam_busy = False


class DialogueCameraGuard(Entity):
    def __init__(self):
        super().__init__()
        self.wrong_for = 0.0
        self.rescues = 0

    def update(self):
        if dialogue_cam_on or dialogue_cam_busy:
            self.wrong_for = 0.0
            return
        # do not interrupt an animation that is still legitimately running
        animator = getattr(camera, 'fov_animator', None)
        if animator is not None and getattr(animator, 'is_playing', False):
            self.wrong_for = 0.0
            return

        # the FOV goes back immediately
        if abs(camera.fov - GAMEPLAY_FOV) > 0.01:
            camera.fov = GAMEPLAY_FOV

        self.check_the_player_is_driving()

    def check_the_player_is_driving(self):
        if game is None:
            return

        if game.state not in ('office', 'apartment', 'house', 'doom',
                              'finale', 'throne', 'ending'):
            self.wrong_for = 0.0
            return

        if _menu_open or _paused_menu or application.paused:
            self.wrong_for = 0.0
            return
        if talk_box is not None and talk_box.open:
            self.wrong_for = 0.0
            return
        if voice is not None and voice.playing:
            self.wrong_for = 0.0
            return
        if death_screen is not None and getattr(death_screen, 'showing', False):
            self.wrong_for = 0.0
            return
        if ceo_screen is not None and getattr(ceo_screen, 'enabled', False):
            self.wrong_for = 0.0
            return
        if getattr(player, 'busy', False):
            self.wrong_for = 0.0
            return
        if getattr(game, 'ending_running', False):
            self.wrong_for = 0.0
            return

        if player.enabled:
            self.wrong_for = 0.0
            return
        self.wrong_for += time.dt
        if self.wrong_for < DIALOGUE_RESET_AFTER:
            return
        self.put_everything_back()

    def put_everything_back(self):
        self.wrong_for = 0.0
        self.rescues += 1
        global dialogue_cam_on, dialogue_cam_busy, dialogue_cam_npc
        dialogue_cam_on = False
        dialogue_cam_busy = False
        dialogue_cam_npc = None
        camera.fov = GAMEPLAY_FOV
        player.enabled = True
        mouse.locked = True
        crosshair.enabled = True
        if player_body:
            player_body.enabled = SHOW_BODY
        try:
            show_viewmodel(player.holding)
        except Exception:
            pass
        set_hud(True)
        print('   camera guard: a conversation left you frozen - everything '
              'reset. Rescue #%d this session.' % self.rescues)


dialogue_camera_guard = DialogueCameraGuard()


def talk_to_npc(target):
    already_met = getattr(target, 'talked', False)
    target.talked = True
    lines = target.talk_lines
    name = getattr(target, 'talk_name', '')
    room = getattr(target, 'npc_room', None)

    # whose voice, and does it loop. talk_voice is a stem set when the village or the house was built, see ROOM_VOICES
    say_with = getattr(target, 'talk_voice', None) or 'npc'
    say_loop = getattr(target, 'talk_voice_loops', True)

    # which of the scientists three speeches, in priority order because more than one can be true:
    #   1. you walked out of the finale having killed nobody - the lease speech
    #   2. this is the first time you have ever spoken to him - the long one
    #   3. anything else - his ordinary lines
    if room == 0:
        if game.pacifist_offer and not game.lease_signed:
            lines, name = SCIENTIST_LEASE, 'THE SCIENTIST'
            # the lease scene is silent, cuz i got lazy and didnt record voice for it
            say_with = None
            say_loop = False
        elif not already_met:
            lines, name = SCIENTIST_FIRST, 'THE SCIENTIST'

    begin_dialogue_camera(target)
    talk_box.start(lines, name, target, voice_clip=say_with,
                   voice_loop=say_loop)


def do_interact():
    # a ringing phone outranks everything else in here. the three guards below can leave you stood in front of it pressing E at nothing
    if (game is not None and game.phone_ringing
            and game.state in ('apartment', 'office')
            and (getattr(look_target(), 'is_phone', False) or phone_in_reach())):
        print('phone: E pressed - answering')
        hand_punch()
        game.answer_phone()
        return

    if player.busy:
        # the busy flag has a watchdog now. an invoke that never arrives used to leave E dead for the rest of the run with nothing on screen saying why
        if time.time() - getattr(player, 'busy_since', 0) < 0.5:
            return
        player.busy = False

    # if somebody is mid-sentence E is next line and nothing else. checked before the raycast so you can look away and still page through
    if talk_box.open and not talk_box.driven_by_voice:
        talk_box.advance()
        return

    if voice.playing:          # E also skips a line of his
        voice.skip()
        return

    hand_punch()
    target = look_target()

    # if the ray missed but somebody is right in front of you that counts, and the same for the phone
    if (not getattr(target, 'is_phone', False) and game.phone_ringing
            and phone_in_reach()):
        target = phone
    if not getattr(target, 'talk_lines', None):
        near = talker_in_reach()
        if near is not None and not getattr(target, 'is_house_door', False) \
                and not getattr(target, 'is_doom_door', False) \
                and not getattr(target, 'is_room_exit', False) \
                and not getattr(target, 'is_phone', False):
            target = near

    # and if you are stood at a door looking at it, you are at a door
    if not is_interactive(target):
        near_door = house_door_in_reach()
        if near_door is not None:
            target = near_door

    if target is None:
        return

    # ANYTHING WITH LINES TALKS, wherever it is standing
    if getattr(target, 'talk_lines', None) and game.state in ('office', 'house'):

        talk_to_npc(target)
    elif getattr(target, 'is_phone', False):
        if game.state in ('apartment', 'office'):
            if game.phone_ringing:
                game.answer_phone()
            elif game.can_replay_call():
                game.answer_phone(replay=True)
        elif game.state == 'finale' and game.finale_choice_ready:
            # only two options now, the phone does nothing here
            flash_notice('shoot him, or walk out. those are the two.', 4.0)
    elif getattr(target, 'is_exit', False):
        if game.state == 'finale' and game.finale_choice_ready:
            game.ending_leave()
    elif getattr(target, 'is_house_door', False):
        # E only. walking into a door does nothing now
        if game.state == 'office':
            game.enter_house(target.house_index)
    elif getattr(target, 'is_room_exit', False):
        if game.state == 'house':
            game.leave_house()
    elif getattr(target, 'is_apartment_door', False):
        # one door, and during the confrontation this IS the way out
        if game.state == 'finale' and game.finale_choice_ready:
            game.ending_leave()
        elif game.state == 'apartment':
            game.leave_apartment()
    elif getattr(target, 'is_apartment_entry', False):
        # and back in again
        game.enter_apartment_from_village()
    elif getattr(target, 'is_throne_exit', False):
        game.leave_throne_room()
    elif getattr(target, 'is_plot_exit', False):
        if game.state == 'ending':
            game.leave_plot()
    elif getattr(target, 'is_doom_door', False):
        # the red door into the DOOM level, also E only now
        if game.state == 'office' and game.door_open:
            game.go_to_doom()
    elif game.phone_ringing and game.state in ('apartment', 'office'):
        gap = distance(phone.world_position, player.world_position)
        flash_notice('the phone is ringing - get closer and press E', 3.0)
        print('   !! phone: E hit %r, not the phone. You are %.2fm away and '
              'PHONE_REACH_RANGE is %.1f'
              % (getattr(target, 'name', type(target).__name__),
                 gap, PHONE_REACH_RANGE))
    else:
        print('   E: nothing interactive here (looking at %r)'
              % getattr(target, 'name', type(target).__name__))


def do_shoot():
    weapons.try_fire()

# SHOOTING PEOPLE OUTSIDE DOOM

VILLAGE_GUN_ON = True
# which scenes you may draw a weapon in. the endings are left out on purpose, shooting the man who just gave you a house is a cooked
GUN_SCENES = ('office', 'doom', 'finale', 'house', 'apartment')
NPC_DEATH_SOUNDS = ['npcdeath1', 'npcdeath2']   # picked at random, found them online
NPC_DEATH_VOLUME = 0.8
NPC_CORPSE_STAYS = True     # False = they vanish instantly, no topple
NPC_DEATH_FALL_TIME = 0.7   # seconds they take to topple
NPC_CORPSE_LINGER = 1.6     # seconds lying there before they start to go
NPC_CORPSE_FADE   = 1.2     # seconds fading out and sinking, then destroyed


def draw_the_gun(out):
    if not VILLAGE_GUN_ON or weapons is None:
        return
    if out:
        # make sure the pistol is the one selected, it is first in WEAPONS and start_with=True
        try:
            weapons.select_slot(1)
        except Exception:
            pass
        player.holding = 'gun'
        show_viewmodel('gun')
        crosshair.enabled = True
    else:
        player.holding = 'hand'
        show_viewmodel('hand')
        crosshair.enabled = False


def is_a_person(entity):
    hop = entity
    for _ in range(4):
        if hop is None:
            return False
        if getattr(hop, 'talk_lines', None) and not getattr(hop, 'dead', False):
            return True
        hop = getattr(hop, 'parent', None)
    return False


def person_root(entity):
    hop = entity
    for _ in range(4):
        if hop is None:
            return entity
        if getattr(hop, 'talk_lines', None):
            return hop
        hop = getattr(hop, 'parent', None)
    return entity


def kill_npc(target):
    who = person_root(target)
    if getattr(who, 'dead', False):
        return
    who.dead = True
    who.talk_lines = None          # E does nothing on a corpse
    who.collider = None            # and you cannot shoot them twice
    name = getattr(who, 'talk_name', 'somebody')
    room = getattr(who, 'npc_room', None)

    # one of my two death sounds, at random
    if NPC_DEATH_SOUNDS:
        clip = load_sound(random.choice(NPC_DEATH_SOUNDS),
                          volume=NPC_DEATH_VOLUME)
        if clip:
            clip.play()

    # the scientist is the only way into the pacifist one, so shooting him closes it.
    if room == 0:
        game.scientist_dead = True
        flash_notice('you have shot the only man who was going to help you.',
                     7.0)
        print('!! THE SCIENTIST IS DEAD - the pacifist ending is now '
              'unreachable this run')
    else:
        flash_notice('%s is dead.' % str(name).lower(), 3.0)

    # take them out of the lists that drive them
    for pool in (villagers, bench_guys, house_npcs):
        if who in pool:
            pool.remove(who)

    if not NPC_CORPSE_STAYS:
        destroy(who)
        return
    # they topple, then fade and sink and get destroyed, so there is no invisible body left for the engine to walk over. NPC_CORPSE_LINGER is how long they lie there
    try:
        who.animate('rotation_z', 88, duration=NPC_DEATH_FALL_TIME,
                    curve=curve.out_bounce)
        who.animate_y(who.y + 0.15, duration=NPC_DEATH_FALL_TIME * 0.4)
        gone_at = NPC_DEATH_FALL_TIME + NPC_CORPSE_LINGER
        who.animate('alpha', 0, duration=NPC_CORPSE_FADE, delay=gone_at)
        who.animate_y(who.y - 0.6, duration=NPC_CORPSE_FADE, delay=gone_at)
        destroy(who, delay=gone_at + NPC_CORPSE_FADE + 0.1)
    except Exception:
        destroy(who)


# the warp keys. all of this only responds while DEV_MODE is True at the top of the file, for testing that everything works pretty much
TEST_STOPS = ['office', 'cemetery', 'doom0', 'doom1', 'doom2', 'doom3',
              'doom4', 'finale']
_test_at = 0
test_label = Text('', parent=camera.ui, origin=(0, 0), position=(0, 0.33),
                  scale=0.8, color=RGB(120, 220, 255), enabled=False)


def test_note(msg):
    test_label.text = msg
    test_label.enabled = True
    invoke(setattr, test_label, 'enabled', False, delay=2.5)
    print('[TEST]', msg)


def test_skip():
    global _test_at
    _test_at = (_test_at + 1) % len(TEST_STOPS)
    stop = TEST_STOPS[_test_at]
    voice.stop()
    fade.alpha = 0

    if stop == 'office':
        game.chapter = 0
        game.level_index = 0
        game.enter_office()
    elif stop == 'cemetery':
        game.enter_office()

        place_player(cemetery_spawn_point())
        game.office_pull = 0.0
        game.phone_ringing = False
    elif stop.startswith('doom'):
        game.level_index = int(stop[-1])
        game.chapter = min(game.level_index, len(CHAPTERS) - 1)
        game.enter_doom()
    elif stop == 'finale':
        game.level_index = len(LEVELS)
        game.enter_finale()
    test_note(f'TEST  ->  {stop}')


def test_spawn_all():
    if game.state != 'doom':
        test_note('go to a DOOM level first (F1)')
        return
    forward = Vec3(camera.forward.x, 0, camera.forward.z).normalized()
    side = Vec3(-forward.z, 0, forward.x)
    for i, tier in enumerate(ENEMY_TIERS):
        spot = player.world_position + forward * 9 + side * (i * 3.5 - 5)
        down = raycast(spot + Vec3(0, 4, 0), Vec3(0, -1, 0), distance=14,
                       ignore=(player,))
        if down.hit:
            spot = down.world_point
        game.enemies.append(DoomEnemy(spot, tier, 1.0))
    test_note('spawned: ' + ', '.join(ENEMY_TIERS))


def warp_to(where, level=0):
    voice.stop()
    fade.alpha = 0
    if where == 'office':
        game.chapter = 0
        game.level_index = 0
        game.enter_office()
        test_note('WARP  ->  office')
    elif where == 'doom':
        if held_keys['shift']:
            level += 1
        game.level_index = min(level, len(LEVELS) - 1)
        game.chapter = min(game.level_index, len(CHAPTERS) - 1)
        game.enter_doom()
        test_note(f'WARP  ->  DOOM level {game.level_index + 1}')
    elif where == 'finale':
        game.level_index = len(LEVELS)
        game.enter_finale()
        test_note('WARP  ->  finale')

# F1 TO F10 - JUMP TO ANY STAGE
#   F1  the apartment, from the start        F6  the confrontation, killer
#   F2  the village                          F7  the confrontation, pacifist
#   F3  DOOM level 1                         F8  the throne room ending
#   F4  DOOM level 3                         F9  the old house ending
#   F5  DOOM level 5, the survival           F10 the CEO of the universe
# # F11 is still fullscreen and Y still quits
# # F6 gives you seventeen livers and F7 gives you none
def warp_stage(n):
    voice.stop()
    talk_box.close()
    fade.alpha = 0
    g = game
    if n == 1:
        g.chapter = 0
        g.level_index = 0
        g.livers = 0
        refresh_livers()
        g.enter_apartment()
        test_note('F1  ->  the apartment')
    elif n == 2:
        g.chapter = 0
        g.level_index = 0
        g.door_open = True
        g.enter_office()
        test_note('F2  ->  the village')
    elif n in (3, 4, 5):
        g.level_index = {3: 0, 4: 2, 5: 4}[n]
        g.chapter = min(g.level_index, len(CHAPTERS) - 1)
        g.enter_doom()
        test_note('F%d  ->  DOOM level %d' % (n, g.level_index + 1))
    elif n in (6, 7):
        g.level_index = len(LEVELS)
        g.livers = 17 if n == 6 else 0
        refresh_livers()
        g.enter_finale()
        test_note('F%d  ->  the confrontation, %s'
                  % (n, 'having killed' if n == 6 else 'having killed NOBODY'))
    elif n == 8:
        g.livers = 17
        g.bought_house = True
        g.lease_from_dj = True
        refresh_livers()
        g.ending_running = False
        g.enter_throne_room()
        test_note('F8  ->  the throne room ending')
    elif n == 9:
        g.livers = 0
        g.pacifist_offer = True
        g.lease_signed = True
        g.ending_running = False
        refresh_livers()
        g.ending_owned()
        test_note('F9  ->  the old house ending')
    elif n == 10:
        g.ending_running = False
        g.boss_killed = True
        g.state = 'doom'
        g.ending_ceo()
        test_note('F10 ->  the CEO of the universe')

# WHAT IS THAT TEXTURE CALLED?
# point at anything and press V. it tells me the texture name, the full path, the pixel size and the group name
# the group name is the one that matters, it is what lets me find the right line in VILLAGE_TEXTURES. saved me hours
def probe_texture():
    hit = raycast(camera.world_position, camera.forward, distance=300,
                  ignore=[player] + no_climb_boxes)
    if not hit.hit:
        flash_notice('nothing in front of you')
        print('[V] nothing hit')
        return
    e = hit.entity
    tex = getattr(e, 'texture', None)
    name = getattr(tex, 'name', None) or (str(tex) if tex else None)
    path = getattr(tex, 'path', None)
    size = ''
    try:
        size = '  %dx%d' % (tex.width, tex.height)
    except Exception:
        pass
    group = (getattr(e, 'group_name', None) or getattr(e, 'material_name', None)
             or getattr(e, 'name', None) or '?')
    if name:
        msg = '%s%s' % (name, size)
    else:
        msg = 'NO TEXTURE - flat colour %s' % (getattr(e, 'color', ''),)
    flash_notice('[V]  %s' % msg, 7.0)
    print('\n--- [V] texture probe ---------------------------------------')
    print('  texture name : %s' % (name or '(none - untextured)'))
    print('  file on disk : %s' % (path or '(not loaded from a file)'))
    print('  pixels       : %s' % (size.strip() or 'n/a'))
    print('  material     : %s' % group)
    print('  entity       : %s' % type(e).__name__)
    print('  distance     : %.2f m' % hit.distance)
    if path is None and name:
        found = find_image(None, str(name))
        if found:
            print('  found as     : %s' % found)
    print('------------------------------------------------------------\n')


GODMODE = False




# F4 - THE STARTUP REPORT

def toggle_godmode():
    global GODMODE
    GODMODE = not GODMODE
    if GODMODE:
        player.collider = None
        player.gravity = 0
        player.health = PLAYER_MAX_HP
        refresh_health()
        test_note('GODMODE ON')
    else:
        player.gravity = 1
        movement.set_eye_height(game.state if game.state in EYE_HEIGHT else 'doom')
        test_note('godmode off')


def test_all_weapons():
    for spec in WEAPONS:
        weapons.owned.add(spec['key'])
    weapons.select(WEAPONS[0]['key'])
    refresh_weapon_hud()
    test_note('all weapons')


def test_report():
    print('\n--- asset report ---')
    models = [OFFICE_GLB, ANGLER_GLB, 'pistol_9mm']
    for name in dict.fromkeys(models):
        print(f'   {name:<20} {"ok" if find_asset(name + ".glb") else "MISSING"}')
    # the enemies are sprites now, so what matters is how many frames landed
    for tier, spec in ENEMY_TIERS.items():
        p = spec['sprite']
        frames = _sprite_index.get(p, {})
        views = sum(len(v) for v in frames.values())
        print(f'   {tier:<9} {p}  {len(frames):>2} frames / {views:>3} views  '
              f'{"ok" if frames else "MISSING - no " + p + "*.png in sprites/"}')
    print(f'   {FRIEND_MODEL:<20} '
          f'{"ok" if find_asset(FRIEND_MODEL + ".obj") else "MISSING"}')
    print(f'   {"hands":<20} {"ok" if hands_rig else "MISSING"}')
    print(f'   {"body":<20} {"ok" if player_body else "MISSING"}')
    print(f'   {"DOOM map":<20} {"ok" if _doom_built else "not built yet"}')
    print(f'   eye height now {movement.eye:.2f}m, DOOM ceiling '
          f'{DOOM_CEILING_UNITS * DOOM_SCALE:.2f}m')
    print('--- end report ---\n')
    test_note('asset report printed to the console')



# INPUT AND THE FRAME LOOP
GUN_NUDGE_KEYS = ('i', 'j', 'k', 'l', 'u', 'o', 'y', 'h', 'n', 'm', 'p') #no longer in game


def input(key):
    # the thanks card clears on anything, and it sits above the menu guard on purpose. key-up events are ignored or the keypress that started the ending clears it
    if thanks_card.enabled and not str(key).endswith(' up'):
        hide_thanks_card()
        return

    if _menu_open or _paused_menu:
        return
    if gun_nudger.on and key in GUN_NUDGE_KEYS:
        return

    if key == 'e':
        do_interact()
    # space in mid-air is the second jump. on the ground ursinas own controller has already handled it
    if key == 'space' and not getattr(player, 'grounded', True):
        movement.try_double_jump()
    if key == 'h':
        player.creepy = (player.creepy + 1) % 3
        if player.holding == 'hand':
            show_viewmodel('hand')
    # dev only. T and P are letters a player WILL press by accident
    if DEV_MODE:
        if key == 'v':                          # name that texture
            probe_texture()
        if key in ('t', 'p'):                   # print coordinates, for building
            pp = player.position
            msg = f"x={pp.x:.2f}  y={pp.y:.2f}  z={pp.z:.2f}"
            print("POSITION:", msg)
            print_on_screen(msg, position=(-0.2, 0.45), duration=1)
    # the X key is gone on purpose. closing an advert has to be done with the MOUSE from the menu or it kills the joke. AD_CLICK_ANYWHERE is the mercy dial
    if key == 'f':
        window.fps_counter.enabled = not window.fps_counter.enabled #for fps toggle
    if key == 'f11':
        # my own toggle, not ursinas. ursinas setter overwrites windowed_size with whatever the window is at that moment, so one F11 made it wrong forever
        set_window_fullscreen(not IS_FULLSCREEN)
        print('window: %s' % ('fullscreen' if IS_FULLSCREEN else 'windowed'))
    # F10 is a stage now, so quitting is Y
    if key == 'y':
        application.quit()

    # dev only. F12 puts the water gun in my hands so i can check the model without playing through to the pickup, watergun was super annoyign to get right
    if DEV_MODE and key == 'f12':
        if weapons is None:
            print('!! weapons are not built yet')
        else:
            weapons.unlock('watergun', announce=True)
            weapons.select('watergun')
            g = weapons.by_key.get('watergun')
            if g is not None:
                print('[F12] WATER GUN: model=%r scale=%.5f pos=%s rot=%s '
                      'damage=%.2f (the rifle is %.2f)'
                      % (g.spec['model'], g.spec['scale'], tuple(g.spec['pos']),
                         tuple(g.spec['rot']), g.spec['damage'],
                         next(w['damage'] for w in WEAPONS if w['key'] == 'rifle')))
                if g.model is None:
                    print('   !! the model did NOT load - check '
                          'lowpoly_watergun.glb is in the project')
            flash_title('WATER GUN  (F12)', 1.6)

    # U is god mode and it is NOT a dev key, i wanted it in the shipped game, cuz i think the game is super buggy and its just easier for someone jut wanting to see the features and get through the game
    if key == 'u':
        toggle_godmode()

    # everything below is developer only, see DEV_MODE at the top. the functions are all still here, only the keys are off
    elif DEV_MODE and key in ('f1', 'f2', 'f3', 'f4', 'f5',
                              'f6', 'f7', 'f8', 'f9', 'f10'):
        warp_stage(int(key[1:]))
    elif DEV_MODE and key == 'b':
        toggle_collider_view()
    elif DEV_MODE and key == TROPHY_TEST_KEY:
        # J hands out trophies so i can test the endings, each press gives the next one i have not got
        left = [t for t in TROPHY_ORDER if t not in SAVE.get('trophies', [])]
        if left:
            unlock_trophy(left[0])
            print('   TEST: gave you %r. Press %s again for the next one.'
                  % (left[0], TROPHY_TEST_KEY.upper()))
        else:
            print('   TEST: you already have all %d trophies. Shift+%s wipes '
                  'them.' % (len(TROPHY_ORDER), TROPHY_TEST_KEY.upper()))
    elif DEV_MODE and key == 'shift+' + TROPHY_TEST_KEY:
        SAVE['trophies'] = []
        write_save()
        print('   TEST: trophies wiped.')

    # WEAPONS. the models, sounds and icons are from mandaw2014s Sandbox (MIT), in the weapons folder
    # every gun shares one small palette image, level.png, which is what their .mtl files point at
    if player.holding == 'gun':
        if key == 'left mouse down':
            do_shoot()
        elif key == 'scroll up':
            weapons.cycle(1)
        elif key == 'scroll down':
            weapons.cycle(-1)
        elif key in ('1', '2', '3', '4', '5'):
            weapons.select_slot(int(key))
        elif key in ('scroll down', '0') or key == 'q':
            pass
    # outside DOOM the gun is something you DRAW. the wheel or 1 brings it out, the same again puts it away
    elif (VILLAGE_GUN_ON and game is not None
          and game.state in GUN_SCENES
          and not talk_box.open and not dialogue_cam_on):
        if key in ('scroll up', 'scroll down', '1'):
            draw_the_gun(True)
        elif key in ('h', '2', '3', '4', '5'):
            draw_the_gun(False)


class MovementController(Entity):
    def __init__(self):
        super().__init__()
        self.lean = 0.0            # -1 left, +1 right - no longer in the game cuz lean is not good
        self.crouch = 0.0          # 0 standing, 1 fully down
        self.bob_t = 0.0
        self.air_jumps_left = 0    # double jump - see try_double_jump()
        # how many air jumps THIS SCENE allows, set from DOUBLE_JUMP_SCENES
        self.max_air_jumps = 0
        self.was_grounded = True
        self.base_speed = OFFICE_SPEED
        self.sprinting = False
        self.eye = PLAYER_HEIGHT

    def set_base_speed(self, speed):
        self.base_speed = speed

    def try_double_jump(self):
        if self.air_jumps_left <= 0 or GODMODE or not player.enabled:
            return False
        self.air_jumps_left -= 1

        # the first jump is one of ursinas animations and if it is mid-flight it is still writing y. stop it or it fights the impulse
        animator = getattr(player, 'y_animator', None)
        if animator is not None:
            try:
                animator.pause()
            except Exception:
                pass
        player.jumping = False

        gravity = getattr(player, 'gravity', 1) or 1
        launch_speed = math.sqrt(50.0 * gravity * DOUBLE_JUMP_HEIGHT)
        player.air_time = -launch_speed / 100.0

        beep(pitch=6, length=0.10, wave='sine', volume=0.25)
        return True

    def set_eye_height(self, scene_name):
        self.eye = EYE_HEIGHT.get(scene_name, PLAYER_HEIGHT)
        player.height = self.eye
        # the collider has to follow, or you clip through low doorways
        player.collider = BoxCollider(player, Vec3(0, self.eye / 2, 0),
                                      Vec3(0.55, self.eye, 0.55))
        # DOOM gets 1.5x jump height, its ledges are chunky.
        player.jump_height = JUMP_HEIGHT * (DOOM_JUMP_MULT if scene_name == 'doom' else 1.0)
        # the double jump is a DOOM ability. outside DOOM this is 0 and space in mid-air does nothing at all
        self.max_air_jumps = (DOUBLE_JUMPS if scene_name in DOUBLE_JUMP_SCENES
                              else 0)
        self.air_jumps_left = 0
        self.was_grounded = True

    def update(self):
        if _menu_open or application.paused:
            return
        # nothing of yours moves during a conversation, the camera is off your head and round in front of somebodys face
        if dialogue_cam_on:
            return

        # godmode flight
        if GODMODE:
            fly = 9.0 * time.dt
            if held_keys['space']:
                player.y += fly
            if held_keys['c'] or held_keys['control'] or held_keys['left control']:
                player.y -= fly
            player.speed = self.base_speed * (SPRINT_MULT if held_keys['shift'] else 1.0)
            player.camera_pivot.y = self.eye
            return

        # you get your air jumps the moment your feet leave the ground, so walking off a ledge works too
        grounded = getattr(player, 'grounded', True)
        # max_air_jumps, not DOUBLE_JUMPS - it is 0 outside the DOOM levels
        if grounded:
            self.air_jumps_left = self.max_air_jumps
        self.was_grounded = grounded

        # crouch
        want_crouch = held_keys['control'] or held_keys['left control'] or held_keys['c']
        self.crouch = lerp(self.crouch, 1.0 if want_crouch else 0.0,
                           min(1, time.dt * 11))

        # sprint (not while crouched, and only going forwards)
        self.sprinting = (held_keys['shift'] and held_keys['w'] > 0
                          and self.crouch < 0.35)

        speed = self.base_speed
        if self.sprinting:
            speed *= SPRINT_MULT
        speed *= 1 - (1 - CROUCH_MULT) * self.crouch
        player.speed = speed

        # leaning is gone. self.lean is held at 0 rather than deleted because the camera pivot below still adds it in, and it frees E completely - E used to be lean AND interact
        if LEAN_ENABLED:
            want = 0
            if held_keys['q']:
                want -= 1
            if held_keys['e'] and not player.can_interact:
                want += 1
            if want:                   # don't lean into a wall
                side = camera.right * want
                if raycast(camera.world_position, side, distance=1.1,
                           ignore=(player,)).hit:
                    want = 0
            self.lean = lerp(self.lean, want, min(1, time.dt * LEAN_SPEED))
        else:
            self.lean = 0.0

        # put it all together on the camera pivot
        eye = self.eye - (self.eye - self.eye * 0.55) * self.crouch

        grounded = getattr(player, 'grounded', True)
        walking = getattr(player, 'direction', Vec3(0, 0, 0)).length() > 0
        if walking and grounded:
            rate = BOB_SPEED * (1.35 if self.sprinting else 1.0)
            self.bob_t += time.dt * rate
            bob = -abs(math.sin(self.bob_t)) * BOB_AMOUNT * (1.5 if self.sprinting else 1.0)
            sway = math.sin(self.bob_t * 0.5) * BOB_AMOUNT * 0.5
        else:
            self.bob_t = 0.0
            bob = math.sin(time.time() * 1.5) * 0.006
            sway = 0.0

        player.camera_pivot.y = lerp(player.camera_pivot.y, eye + bob, min(1, time.dt * 14))
        player.camera_pivot.x = lerp(player.camera_pivot.x,
                                     self.lean * LEAN_SHIFT + sway, min(1, time.dt * 12))
        player.camera_pivot.rotation_z = -self.lean * LEAN_ANGLE


movement = MovementController()


def apply_camera_shake():
    global _shake_amount
    if _shake_amount <= 0.0001:
        return
    camera.x = random.uniform(-_shake_amount, _shake_amount)
    camera.y = random.uniform(-_shake_amount, _shake_amount)
    _shake_amount = lerp(_shake_amount, 0, min(1, time.dt * 12))
    if _shake_amount <= 0.0001:
        camera.position = (0, 0, 0)


def update():
    if _menu_open or application.paused or _paused_menu:
        return

    step_assist()
    apply_camera_shake()

    # is E going to do something right now. it uses the SAME ray do_interact() uses, so the prompt cannot promise something E will not do
    looking_at = look_target()
    _guy_near = (not talk_box.open and talker_in_reach() is not None)
    # the phone by proximity as well as by aim. the desks own boxes and the no-climb pillars can stop a ray before it reaches the handset
    _phone_near = phone_in_reach()
    if not is_interactive(looking_at):
        _near_door = house_door_in_reach()
        if _near_door is not None:
            looking_at = _near_door
    player.can_interact = bool(voice.playing
                               or talk_box.open
                               or _guy_near
                               or getattr(looking_at, 'is_phone', False)
                               or getattr(looking_at, 'is_exit', False)
                               or getattr(looking_at, 'is_house_door', False)
                               or getattr(looking_at, 'is_room_exit', False)
                               or getattr(looking_at, 'is_doom_door', False)
                               or getattr(looking_at, 'is_apartment_door', False)
                               or getattr(looking_at, 'is_apartment_entry', False)
                               or getattr(looking_at, 'is_throne_exit', False)
                               or getattr(looking_at, 'is_plot_exit', False)
                               or getattr(looking_at, 'talk_lines', None))

    # holding the trigger keeps firing, which is what the minigun is for
    if held_keys['left mouse'] and player.holding == 'gun' and weapons.current:
        weapons.try_fire()

    # while he is talking the box has its own [E] prompt, so the floating one gets out of the way
    if talk_box.open:
        show_prompt('')
    # contextual prompts, so you always know what E does
    elif getattr(looking_at, 'talk_lines', None) or _guy_near:
        show_prompt('[E]  talk')
    elif game.state == 'office' and getattr(looking_at, 'is_house_door', False):
        # your own house says so instead of pretending it will open
        _need = HOUSE_LOCKED_UNTIL.get(looking_at.house_index)
        if _need is not None and _need not in game.houses_visited:
            show_prompt(HOUSE_LOCKED_MESSAGE)
        else:
            show_prompt('[E]  enter house %d' % (looking_at.house_index + 1))
    elif getattr(looking_at, 'is_apartment_door', False):
        show_prompt('[E]  go outside' if not game.phone_ringing
                    else 'the phone is still ringing')
    elif getattr(looking_at, 'is_apartment_entry', False):
        show_prompt('[E]  go home')
    elif getattr(looking_at, 'is_plot_exit', False):
        show_prompt('[E]  back to the village')
    elif getattr(looking_at, 'is_throne_exit', False):
        show_prompt('[E]  back to the village')
    elif game.state == 'office' and getattr(looking_at, 'is_doom_door', False):
        show_prompt('[E]  go through')
    elif game.state == 'house':
        show_prompt('[E]  leave' if getattr(looking_at, 'is_room_exit', False)
                    else 'the door leads back out')
    elif game.state in ('apartment', 'office') and game.phone_ringing \
            and not voice.playing:
        # and the prompt, which was gated on the same wrong state
        if getattr(looking_at, 'is_phone', False) or _phone_near:
            show_prompt('[E]  answer it')
        else:
            show_prompt('it is ringing')

    if game.state == 'finale' and game.finale_choice_ready:
        if getattr(looking_at, 'is_phone', False):
            show_prompt('[E]  pick it up again')
        elif getattr(looking_at, 'is_exit', False):
            show_prompt('[E]  leave')
        else:
            show_prompt('shoot him   /   walk out   /   ...')


# THE LAST FEW THINGS BEFORE app.run() - ALMOST DONEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE



# scan the sprite folder before anything can ask for a frame. it prints what it found so a missing set shows up at startup
print('textures: detail %r (x%.2f on every image). The levels are: %s. '
      'Run "python launcher.py potato" for the fastest one.'
      % (TEXTURE_DETAIL, texture_detail_scale(),
         ', '.join(TEXTURE_DETAIL_LEVELS)))

_idx = build_sprite_index()


# everything is built by now, so this is the only moment the full entity list exists
freeze_static_entities()


# THE ENGINE HAS TO BE TOLD WHERE input() AND update() ACTUALLY LIVE

# ursina does import __main__ ONCE, when ursina itself is imported, and from then on every key goes to __main__.input(key) and every frame to __main__.update()
# run this file on its own and __main__ IS this file, which is why it always worked on my machine and only broke once the project got a launcher
# through launcher.py the module ursina is holding is launcher.py, which has neither of them, so E was dead EVERYWHERE and nothing errored anywhere
# so i hand them over myself rather than trusting it to have picked the right module
def install_engine_hooks():
    here = globals()
    targets = []

    # whatever python currently calls the main script
    main_now = sys.modules.get('__main__')
    if main_now is not None:
        targets.append(main_now)

    # and the module object ursina grabbed for itself, which through the launcher is a different one
    engine = sys.modules.get('ursina.main')
    if engine is not None:
        held = getattr(engine, '__main__', None)
        if held is not None:
            targets.append(held)

    attached = 0
    for mod in targets:
        if getattr(mod, '__dict__', None) is here:
            continue                 # that one is this file - already right
        mod.input = input            # the E key, the mouse, every key in here
        mod.update = update          # prompts, step assist, hold-to-fire
        attached += 1
    if attached:
        print('input hooks: attached to %d other module(s) - E reaches the '
              'game through the launcher now' % attached)
    else:
        print('input hooks: running as __main__, nothing to re-attach')


install_engine_hooks()
app.run()
