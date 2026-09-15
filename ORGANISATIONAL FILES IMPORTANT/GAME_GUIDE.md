# Game guide/ explanation of what the hell this game is

My final project for Tech Basics I. It is a first person game made in Python with the Ursina engine.

You are broke and you rent one room. The phone on the desk is ringing.
A man from a company offers you four hundred euros for every life you take inside an old 1993 shooter, because the businessmen in there
have rewired themselves into the game, they can afford to be rebuilt themselves three or four times, so that's about how many levels there are. 
What you actually want is the house at the end of the village, to finally find yourself.
## How to play

You start in the menu, where i first implemented my style and I quote -
"a surreal, "sensorally aggressive" and maximalist retro aesthetic that blends low-poly PlayStation 1 
hardware limitations with a chaotic "shitpost" internet culture vibe"

Press play(if you can find the button for it) and you wake up in the room you rent. The phone
on the desk is ringing. Walk up to it and press E and keep pressing E to get
through what he says to you.

The opening call and apartment is supposed ot subtly or not su subtly give you an overview what is 
going on in this games universe and what kind of a person are you.

After the phone call you can leave the flat and explore the village. Five of
the houses have an interactable door you can open with E, and the people walking around will
talk at you if you press E on them. (be aware it might not be intelligable dialogue)

The house at the end of the village with the
sign on, is the one you are trying to buy and are working towards in the game story.

Somewhere in the village there is a RED DOOR. That is the way into the job. Press
E on it and you are in DOOM E1M1. Now in there you are getting paid per person. Find
the key, find the exit, get out. Then you are back in your room and the phone
rings again.

That happens five times and then there is the confrontation, and then the game
ends in one of three ways.

## Some things worth knowing: 

I HIGHLY RECOMMEND USING "U" TO GET INTO GOD MODE, because in the doom level, you can easily get out of the ceiling
of the map, this feature, on second thought after Jasper Steinberg Playtested it, would be a good speedrunning strategy,
because in differnet parts of the doom level, you can get back into the world through colliders(i won't say where),
but this would add another dimension to the game, which can be explored and I would rather not take it out, so
I will leave the doom ceilings broken as they are.



This doesn't break the game because the fail safes in falling off the map still work, and the game can be completed
without cheating and using the god mode, but it's also completable if you get out of the designated map!



although it's worth mentioning that there are a lot more stuff broken in this game with colliders,
that are not intentional i just didn't have time or energy or simply will power ot fix everything.




The adverts that appear over the screen do not close with E.
You have to PAUSE with escape and then click the little red X on the advert.
This is purely to annoy the player, also because the player is wearing meta glasses and the ads just pop up.

There is a number in the corner of the screen that counts how many livers you have harvested.

The game has floors that hurt you in the DOOM levels, the green sludge. Do not
stand in it, it might also crash the game, which I think matches the aesthetic.

You can jump twice in the DOOM levels, but only there.

Press F if you want to see the framerate, and start the game with
`python launcher.py potato` if it is bad.


## The three endings

The game only tracks two things at the end: did you kill the boss, and how many
livers are you carrying.

Kill the man at the confrontation and you get a depressed ending

Finish with livers on you and you get the ending where you took the livers, still depressed

Finish with ZERO livers - which means killing nobody in the entire game - and the
scientist signs your lease and you get an exclusive house. This is the hidden one and it is
the point of the whole game, revealed in the text box messages of each ending.

The title screen shows you bits of text from the endings you have NOT got yet,
which is the only hint that there is more than one, that and the different trophies.

Trophies save to a file in your own home folder, not in the game folder, so a
fresh copy of the game starts with nothing unlocked. On Windows that is
`C:\Users\yourname\.thefifthnail\save_state.json`. 


## How the code works

`launcher.py` is the launcher. `src/game.py` is the whole game

The game runs top to bottom ONCE, building everything, and the last line is
`app.run()` which starts the frame loop. That matters more than it sounds, because
it means there is no such thing as loading a level. 

There are five or six ideas that explain most of it, everything else is explained in comments.

**Assets are found by name, not by path.** `find_asset('villagerMODEL.obj')`
searches an index of the entire project that gets built by one walk through the
folders when the game starts. So i can move nearly any file into any folder and
the game still finds it, as long as i do not rename the file. 

Three folders are the exception they are found by their folder name instead, so do not rename these:
`village` (because village_nav.json is loaded relative to it), `DOOM_E1M1` (the
map and its 58 textures) and `sprites` (the enemy sprite sheets).

**MADE WITH AI AND ITS ALL OVER THE CODE A missing file is a warning, never a crash.** Every loader prints `!!` and the
name of what it wanted and then carries on. So the game always starts and i can
see what is missing instead of reading a traceback. This is explained more in the game.py file comments

**This is a check** and its under almost every function, it's one of many failsafes i have in the code so i wouldn't get mindlessly
stuck on problems that i have no idea are even problems, so this failsafe prints nicely in the output if something is missing

**Scenes are roots that get enabled and disabled.** `office_root`, `doom_root`,
`city_root`, `house_root`, `apartment_root`. Everything hangs off one of those.
`clear_scenes()` turns them all off.
That is the entire scene system.

**Anything that stands still costs nothing.** Just before `app.run()` there is a
pass that sets `ignore=True` on every entity that has no update function of its
own. Ursina checks `ignore` first in its frame loop, so those get skipped
completely. 

THIS IS SUPER IMPORTANT, because right now the game is horribly optimised and laggy so this helps a bit 

**Every scale is measured, not typed.** Models turn up in completely different
units - one tree was 1100 units tall and a bench was 1.0. Nothing in the game has
a scale i guessed. It reads the model's real bounding box and scales it to a height
in metres.


## Where the code is

The file is cut into sections and each one has UPPER CASE LETTERS with a name for a bit better coordination in going through  the code. 
but control f is generally more fruitful way to go through the code.

the most important ones are these - 

DEV_MODE, then GAME START (the app, window, resolution, fullscreen), WINDOW MODE,
TUNING, THE SCRIPT, LEVEL TABLE, HELPERS, MODEL LOADING, PLAYER MOVEMENT, PLAYER
BODY, FIRST PERSON HANDS, WEAPONS, UI, VOICE, THE OFFICE, THE DOOM LEVEL, GARDEN
AND HOUSE, THE VILLAGE, THE FIVE NPC HOUSES, NPCS, THE MENU, GAME STATE MACHINE,
INTERACTION, and INPUT AND THE FRAME LOOP.


## Where to change things

Any number at all - speed, damage, size, distance, positions - is in
TUNING at the top of the file, i have to say it is the smartest thing i have ever thought of (i stole the ideafrom a basic tutorial)

What somebody says is in THE SCRIPT mostly.

A gun's damage or how fast it fires is the `WEAPONS` list in TUNING.

House textures are `HOUSE_WALL_TEXTURES` in TUNING. - i never ended up making the house textures crazy, which was my original idea, they are just original from the asset unfortunately.

Villagers are all on `VILLAGERS` list.
The menu text is `MENU_PARAGRAPHS` and `MENU_ENDING_SNIPPETS`.

To turn test keys back on set `DEV_MODE = True` at the top. That gives you F1
to F10 to warp between stages, F12 for the water gun, B to see the colliders, V to
probe a texture, T and P to print your own coordinates, G to nudge the gun
position, J for the trophies and TAB for the editor camera.

To make it run faster: `RESOLUTION_SCALE`, `VILLAGE_FLOOR_STEP` and `CLIP_FAR`. If
you can walk through a gap in the village that should be solid, `VILLAGE_GAP_MAX`.(this is still very broken as many things in the game, i will get into it later)

## more on features that are useless, not working in the read me!