# References

Everything not noted in this document belongs to me and was made on 
one of the following programs and is in the project files: Blender, Paint, Figma, Occasionally on Davinci picture edit. 
Models, sounds, fonts and code, with whoever made it, the licence and a link.

Almost all of the models came from Sketchfab and some of them are CC BY 4.0,
which means i can use them and change them as long as i credit the person who made
it, which is what this file is for. Some of the Assets are also usable and do not have to be credited
I have therefore not wirtten them down, there would be a tooooon of them.

If the licence is something else i have
written it next to the model.


## Engine and libraries

Ursina 7.0.0, by Petter Amland (pokepetter) and contributors, MIT
https://github.com/pokepetter/ursina

Panda3D 1.10.14, Carnegie Mellon ETC and the Panda3D community, modified BSD
https://www.panda3d.org/

panda3d-gltf 1.2.0, by Mitchell Stokes (Moguri), BSD-3-Clause
https://github.com/Moguri/panda3d-gltf

Pillow, by Jeffrey A. Clark and contributors, MIT-CMU
https://python-pillow.org/

Python 3.12, Python Software Foundation

Two prefabs that come with ursina and do a lot of work in my game, both covered by
ursina's MIT licence: `FirstPersonController` from
`ursina.prefabs.first_person_controller`, which is all of the player walking,
gravity and mouse look, and `ursfx` from `ursina.prefabs.ursfx`, which makes the
little beeps and shooting noises at runtime instead of from a file.

Programs i used to make and fix the assets, which do not put any conditions on the
game itself but leave their name inside the files: Blender
(https://www.blender.org/), GZDoom Builder (https://zdoom.org/), QuadSpinner Gaea
(https://quadspinner.com/gaea/), gltfpack from meshoptimizer
(https://github.com/zeux/meshoptimizer) and Prisma3D (https://prisma3d.app/).


## Code i borrowed

Sandbox, by Mandaw (mandaw2014), MIT, copyright (c) 2022 Mandaw
https://github.com/mandaw2014/Sandbox

This is the biggest borrowing in the project by far. Sandbox is a first person
shooter demo made in Python on Ursina. My weapon system started as a straight copy
of theirs and i have rewritten it slightly ever since, but the models, the sounds and the HUD
icons are still theirs and still in the game:

pistol.obj, shotgun.obj, rifle.obj, minigun.obj, minigun-barrel.obj,
rocket-launcher.obj, rocket.obj, bullet.obj
pistol.ogg, shotgun.ogg, rifle.ogg, minigun.ogg, rocket_launcher.ogg,
destroyed.ogg, dash.ogg, fall.ogg
pistol-icon.png, shotgun-icon.png, rifle-icon.png, minigun-icon.png, hit.png,
vignette.png, level.png, sky.png, street.jpg
particle.obj, particles.obj, jumppad.obj, enemy.obj, bigenemy.obj
mountainous_valley.obj, desertedsands.obj, floatingislands.obj
Roboto.ttf

MIT says the copyright notice has to ship with anything that uses it, which is why
Sandbox's LICENSE stays in the project.

FPS, also by mandaw2014, MIT
https://github.com/mandaw2014/FPS

I used their head bobbing pattern, but applied to the body instead of the head.
It is credited in the code where i use it too.

P_NewChaseDir, from the original DOOM source code by id Software

This is how DOOM monsters decide which of eight directions to walk in. I read how
the algorithm works and wrote it again in Python, i did not copy the C. It is what
my enemies use. - I ALSO USED AI FOR THIS TO UNDERSTAND IT, BUT I HAVE THIS WRITTEN IN THE CODE COMMENTS ALREADY

Things i wrote from many sources combined like tutorials, rando mwebsites, forums rather than from one source, listed so it is
clear where they came from I AM NOT SURE HOW TO COMBINE THIS I ALSO USED AI TO UNDERSTAND IT
BREAK IT DOWN OR TRANSLATE IT FOR URSINA UDNERSTANDABLE CODE: breadth first search over the village grid to find
which parts connect, object pooling for the sparks, turning down how often distant
things update, decimating meshes by triangle area, splitting a model into limbs by
triangle centroid, and dealing out the villager textures like a deck of cards so
no two villagers next to each other match.


## Models

The village, which is the biggest asset in the game:

village.obj and DachaFAB.obj - "Soviet Villiage" by novusod (the spelling is
theirs), Sketchfab
https://sketchfab.com/3d-models/soviet-villiage-39b1d612a92e478c9197c33a7f232312

People:

villagerMODEL.obj / willong_ps1_horror_style.glb - "Willong PS1 Horror Style" by
kalima33, CC BY 4.0. This one model is every single one of the 39 villagers, they
just each get a different texture.
https://sketchfab.com/3d-models/willong-ps1-horror-style-515612c8e9d34dc49381a86765145394

villagerMODEL2.obj / psx_styled_male.glb - "PSX Styled Male" by GrilledLesser
(pacmanwithteeth), CC BY 4.0
https://sketchfab.com/3d-models/psx-styled-male-3dbc0a950d044458be5ae46392c70d39

psx_base_-_bearded_man.glb and PsxMan.obj - "PSX Base - Bearded Man" by MrPrisma3D,
CC BY 4.0
https://sketchfab.com/3d-models/psx-base-bearded-man-8768af8ecea24bddbd1744af4bc2fb29

psx_man.glb / psx_man.obj - "psx man" by petya-petyavich, CC BY 4.0
https://sketchfab.com/3d-models/psx-man-41b0580d4d5c4cc183cfeae523ea0a09

ps1_psx_high_school_character.glb / .obj - "PS1 PSX High School Character" by
crimsongcat, CC BY 4.0
https://sketchfab.com/3d-models/ps1-psx-high-school-character-d96f74f0dc6f49559083c110fef37e2f

male_01_citizen.glb - "Male_01 Citizen" by Lev0S99k, CC BY 4.0
https://sketchfab.com/3d-models/male-01-citizen-e9286d58207c40c08da0d35d40e670e7

handsatwaist.glb - the same model as above, which i reposed in Blender and
exported again, so it is Lev0S99k's model and the same licence.

monster.glb / monster.obj - "Monster" by Luka25876, CC BY 4.0
https://sketchfab.com/3d-models/monster-95d149388dff47fda5422aa491c28d5c

enemy_verity.glb, veritytm.glb, veritytm_static.glb - "Verity™" by P3G, CC BY 4.0
https://sketchfab.com/3d-models/veritytm-0017a3d968e946bcba84ec107bd1d3ee

enemy_ghoul.glb - "Fallout: Feral Ghoul" by emijar, CC BY 4.0
https://sketchfab.com/3d-models/fallout-feral-ghoul-9f9441a483ca476a8ba54223717404d1

Places:

throne_room.glb - "Throne Room" by LaReinaPam, CC BY 4.0
https://sketchfab.com/3d-models/throne-room-1faee220456a43ab97f899921f9a9046

vandalized_room.glb - "Vandalized Room" by jimbogies, CC BY 4.0
https://sketchfab.com/3d-models/vandalized-room-dbdecb3dae5d4898872880a3a95dcec8

abandoned__building__shop__old__house.glb - "Abandoned | Building | Shop | Old |
House" by Erroratten, CC BY 4.0
https://sketchfab.com/3d-models/abandoned-building-shop-old-house-0ed14367314946b298d9a58db66da040

horror_corridor_vr_room_baked.glb - "Horror Corridor VR room [Baked]" by abhayexe.
This one is the Sketchfab Standard licence, not Creative Commons - the terms are at
https://sketchfab.com/licenses
https://sketchfab.com/3d-models/horror-corridor-vr-room-baked-cb18e0e7f2f84970b6410a1510fcc722

fantasy_wooden_house.glb - "Fantasy wooden house" by pxltiger, CC BY 4.0
https://sketchfab.com/3d-models/fantasy-wooden-house-7530e36a937d445189339aa743a58e55

village_house_lowpoly.glb - "Village house lowpoly" by ajalphaboy, CC BY 4.0
https://sketchfab.com/3d-models/village-house-lowpoly-08714418667a46e48e62249785f9ded8

office_lowpoly.glb - "low-poly office" by DarianDS, CC BY 4.0
https://sketchfab.com/3d-models/low-poly-office-c924672f29df4fd68c3e3b9fd70741fe

backrooms.glb - "Backrooms V2 (LEVEL 0, MADE BY ME IN BLENDER)" by EMPEROR-MARK,
Sketchfab
https://sketchfab.com/3d-models/backrooms-v2-level-0-made-by-me-in-blender-91d707acdfce4d5d940f7cb8c25c6e31

Props:

hospital_bed.glb and bedframe.obj - "Hospital Bed" by Larry3d, CC BY 4.0
https://sketchfab.com/3d-models/hospital-bed-04eec268506d45a192f70aea01b8d292

bench.glb and bench_only.obj - "Bench 5 USSR (Game ready)" by Nikita Filimonov,
CC BY 4.0
https://sketchfab.com/3d-models/bench-5-ussr-game-ready-1ff1e215c1744192bb4ef2df9454927e

dj_set.glb - "DJ Set" by Milan, CC BY-NC-ND 4.0. This is the strictest licence in
the whole project - non commercial only, and it also says no derivatives, and i do
rotate and rescale it, so for anything that was not a student project this one
would have to be replaced.
https://sketchfab.com/3d-models/dj-set-dacd1e338270478485e35f8a79d6dc64

dirty_toilet.glb - "Dirty Toilet" by shedmon, CC BY 4.0
https://sketchfab.com/3d-models/dirty-toilet-389d5427a1f344c4aa4883ec5a6aaf05

still_life.glb - "Still Life [IMPROVED VERSION] - (The Backrooms)" by DocoDummy,
CC BY 4.0
https://sketchfab.com/3d-models/still-life-improved-version-the-backrooms-b8e5427af3cd4be690361d047d803f98

after_work.glb - "After Work" by Duhan, CC BY 4.0
https://sketchfab.com/3d-models/after-work-91451a68dfa847fe9a12d10133ab6d22

trees_low_poly.glb - "Trees Low Poly" by Igor_K., CC BY 4.0
https://sketchfab.com/3d-models/trees-low-poly-1d2dcca2ccb1496c85b7cc5789a2a261

giant_low_poly_tree.glb - "Giant Low Poly Tree" by Sahir Virmani, CC BY 4.0
https://sketchfab.com/3d-models/giant-low-poly-tree-acfd2b7f80894848b56c2ac8e7e59572

Guns:

pistol_9mm.glb and 9mm_pistol.glb - "9mm Pistol" by TORI106, CC BY 4.0
https://sketchfab.com/3d-models/9mm-pistol-43bc09f5aace4346a8a2b6e1580fc03f

heavy_angler.glb - "Heavy Angler LowPoly Gun" by Andrey Mikheev, CC BY 4.0
https://sketchfab.com/3d-models/heavy-angler-lowpoly-gun-4386933e43304f4fb08325d23d2962ff

lowpoly_watergun.glb - "Lowpoly Watergun" by rustard, CC BY 4.0
https://sketchfab.com/3d-models/lowpoly-watergun-c9eb5afe553a4551b958ce8628ccd4f6


## DOOM

doom_E1M1.obj - "Doom E1M1: Hangar - Map" by pancakesbassoondonut, CC BY 4.0.
This is somebody's remake of the level in Blender, which is what i credit here -
but the level itself was designed by John Romero and the textures are id
Software's, so crediting the person who rebuilt the mesh does not give me any
rights in DOOM.
https://sketchfab.com/3d-models/doom-e1m1-hangar-map-2148fb6a3fe7454b901fcea67d70b318

The 58 wall and floor textures in media/DOOM_E1M1 are DOOM's own, you can tell
from the names (BIGDOOR2, BROWN1, COMPTALL, DOORTRAK and so on).

The 1948 sprite frames in media/sprites are in DOOM's naming format (four letters,
then a frame letter, then a rotation number, like AHPOH5) but the four letter
prefixes are not the ones vanilla DOOM uses, so these came out of some community
sprite pack rather than the original game. I could not work out which one, and i
am not going to pretend i know.

DOOM itself: id Software, 1993, now part of ZeniMax / Microsoft.
https://www.idsoftware.com/


## Half-Life models

These are fan made models of Valve's characters. The models are CC BY 4.0 and made
by the people below, but the characters are Valve's.

gman_hd.glb - "Gman HD" by photon, CC BY 4.0
https://sketchfab.com/3d-models/gman-hd-e63efb80b9604e068360bab1a80ace2c

half-life_scientist_einstein.glb - "Half-Life Scientist Einstein" by Rage_Models,
CC BY 4.0
https://sketchfab.com/3d-models/half-life-scientist-einstein-0956ce03b6e0471cae71fbfd880811a6

male_cheaple.obj and male_cheaple_sheet.png - this is Valve's own low resolution
City 17 citizen from Half-Life 2, the one they use for crowds in the distance.
Valve Corporation.
https://www.models-resource.com/pc_computer/halflife2/model/15651/

The first person arms are the same kind of thing - a community rip of the
Half-Life 2 viewmodel arms, used here for a student project and nothing else.


## Audio

THE MUSIC AND AUDIO ARE ALL RECORDING WITH MY PHONE AND ME MAKING NOISES INTO IT
AND THEN PUTTING IT TOGETHER IN "REAPER DAW", SO THIS IS ALL MY ORIGINAL CREATIONS.

THE VOICELINES FOR DIFFERENT CHARACTERS WERE DONE BY ME AND MY BEST FRIEND IN ESTONIA, 

ALSO ULAS HELPED WITH SOME VOICE LINES, BUT THEIR VOICES ARE BARELY HEARD AND ARE
CHANGED UP A LOT BY VOICE CHANGERS.


My own recordings, so no credit needed, listed just so it is clear which is which:
1handler.ogg to 7handler.ogg, ulasturkish.ogg, ulasturkishPC.ogg,
ulasturkishCEOhandler.ogg, ulasturkishCEOhandlerVOICE.ogg, JaakSASSfinal.ogg,
bosskillSASSfinal.ogg, scientistFULLMONOLOGUE.ogg, DJmonologue.ogg,
npc1viimane.ogg, npc2VEELUKS.ogg, npc3JO.ogg, npc3HEY.ogg, npcline1.ogg,
npc_realhuman1.ogg, npc_realhuman2.ogg.

Music that is not mine:

ifIevergetaroundtoliving.ogg - "If I Ever Get Around to Living" by John Mayer,
from Born and Raised, 2012. Sony / Columbia, all rights reserved. This plays on
one of the endings. It is not licensed for use in a game and i would have to
replace it with something royalty free before putting this anywhere public. - but it is played and performed by me in 
the recording

weirdfishesinstrumental.ogg - "Weird Fishes/Arpeggi" by Radiohead, from In - this actually isnt in the game just in the files
Rainbows, 2007, instrumental version. Warner Chappell / XL, all rights reserved.


Sound effects:

npcdeath1.ogg and npcdeath2.ogg - Universfield on Pixabay, Pixabay content
licence, free and no attribution required, but crediting them anyway
https://pixabay.com/users/universfield-28281460/

iphone_alarm.mp3 / .ogg - the stock iOS alarm tone, so Apple's, and not licensed
for redistribution either.

The gun sounds came with Sandbox, see above.




## Fonts

comic sanse is copyrighted by microsoft I actually cant use it, i would swap in Comic Neue by Craig
Rozynski, which is SIL Open Font Licence, looks near enough the same and needs no
code change.
https://comicneue.com/

Roboto.ttf is Google's Roboto, Apache 2.0. It came with Sandbox and the game does
not actually use it.


## Text quoted in the game

Some of the writing on the walls and in the monologues is quoted, used as found
text: Emerson's Self-Reliance, Bataille's The Accursed Share, and some Radiohead
lyrics.


## Mine

Everything else. All of the writing and dialogue, the three endings, the design,
the textures and photographs i made and painted, the menu, the voice recordings
above.
