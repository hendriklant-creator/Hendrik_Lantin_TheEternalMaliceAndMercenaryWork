# Eternal Malice and Mercenary Work

**This game is about late-stage-capitalism.**

## How to install it
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On mac or linux the second line is `source .venv/bin/activate` instead. I USED AI FOR THS IDK HOW MAC WORKS???

That installs ursina, panda3d, panda3d-gltf and Pillow, which are the four things
the game needs.


## How to run it

```
python launcher.py 
```
#Little update updating on 17.09.2026 - Please after downaloding also download the requirements with pip in cmd, i recommend opening the folder in terminal and then doing the necessary steps. 

BE AWARE THE GAME TAKES TIME TO LOAD IT'S BIG, ALSO DONT BE JUMPSCARED BY THE MUSIC

That is the only file you have to run. If the framerate is bad, and on a laptop it
will be, I suggest going to game.py and control f to find the resolution settings and changing it to "potato", or "low"
I have it natively on low so it sohuld be fine, and if its stil llagging then blame my bad code.

There is also

```
python launcher.py loud
```
which prints everything the game loaded and, more importantly, prints `!!` and the
name of every file it could NOT find. That is how i test things. If something looks
wrong, run it loud first. 

## Controls

WASD - walk
SHIFT - sprint
CTRL - crouch
SPACE - jump (in the DOOM levels you can jump twice)
E - interact, and also skip to the next line of talking
LMB - shoot
1 to 5 and the mouse wheel - change weapon
ESC - pause, AND THIS IS HOW YOU CLOSE THE ADVERTS
F - fps counter
F11 - fullscreen
U - god mode!!!!!!!!!!!!!!!!!!!!!! - I highly suggest using this if you accidentally get out of the map, or the enemies are too strong and the game is too laggy.
Y - quit

There are a lot more keys than this but they are my test keys and they are turned
off. `DEV_MODE` at the top of the game file turns them all back on and the comment
next to it says what each one does.

## NOTE ON AI
**EVERYTHING that I used Ai for is explicitly noted in comments, besides that To finalise the game, and for a lot of optimisation,
as well as organising everything into logical way from start to finish I USED AI FOR, Specifically Claude Opus 5.**

## MAKING OF THE GAME

I finished the main code and tinkering at the end of September, and started the coding process in mid July.
I worked on and off for about 2 and a half weeks on it, and I learned S O M U C H, but also i feel like it was very slow and 
working on any other engines it would have been a much more enjoyable process.

I WISH I WOULD HAVE PUT DIFFERENT PARTS of the code into different folders, becuase the 15000 lines of code
is so laggy and confusing, if you don't know where everything is!

I mostly followed the following methodology.

Think of an idea - What would be the easiest way of making it in code - google the idea - REALLY TRY AND LOOK AT TUTORIALS, INSTEAD
OF JUST READY CODE, TO UNDERSTAND THE CONCEPT AS A WHOLE - then go to ready made code and compare tutorials - then as well as before check
Ursina engine code book, which was generally very helpful - and if then I can't figure out how to implement it with my current code,
then I would use AI first to explain what I should do and if I still couldnt't do it then I would let it do it for me in the worst case.


## What is in the game

A village of soviet houses. Five interactable doors open and you
can go inside all five. 39 people walk around who are interactable, and the weather
changes every couple of seconds.

The real DOOM E1M1 map, which i found remade online as an .obj and then rebuilt in
the game one entity per texture. The enemies are real DOOM sprites and they use
DOOM's own eight direction chasing.

Adverts that pop up over the game and will not go away until you pause and click
the little red X, which i think is the funniest thing in the game.

Six weapons, five levels plus a survival one, a boss, a Epileptic's worst nightmare textures MADE BY ME mostly in paint or figma : )

First person hands and an actual body you can see when you look down, with the
legs and arms swinging as you walk, I must prefice this because this took me  WAY TOO LONG TO DO

Three endings - more about that in game guide.


## How the idea came about and a general explanation

It started as just a room with a texture on the wall and a mouse look, because i
wanted to see if Ursina could even do first person, they way i wanted.

Things that changed on the way:

I had a cemetery, backrooms full map, only the doom map for the whole game, 
which eventually just became a village and a doom level. I had a scanned graveyard in first and it was about
900 000 triangles and you could not walk around it at any framerate, so it was a mess.

The office moved indoors. The desk was just standing in the middle of the map at
first. It became a rented flat instead.

The enemies got rewritten. I had .glb monsters and panda3d-gltf crashed on level
two every time. Also they never belonged in E1M1. So I used Real DOOM sprites instead, which was way more fitting.


The idea is mostly inspired by the game Cruelty Squad and its crazy textures and story about seemingly simple 
given things like buying a place to live at, being locked behind horrific deeds. The complete lack of care for human life dignity,
morality is expressed through the voice lines in npc villagers inside and outside of the houses, as well as your handler and pretty much everything interactable.

https://gamestudies.org/2601/articles/tvorundunn

This paper helped me contextualise the art more and get a grasp of what these visuals could be saying beyond just looking funny and unusual.
Contextualising the idea of the supermarket as a Neoliberal Space which we have grown to just accept looking a certain way
really stuck with me. Which is why the flickering sky, crazy villager houses are one of my favourite things in my game, because
understanding the context of the universe where they are located in and the general norms of the people living in it, you start to look past
the absurdity and accept or at the least deal with your living situation. 

In an absurdist case like this game, you deal with harvesting livers and killing entrepreneurs to live a happy life in a residential area 25 square meters trash truck on fridays and no annoying neighbour apartment or house.
This contrast between a absurd universe like this games, and our modern supermarkets as places of absolute manipulation and greed in a tightly packed space of living 
is what still draws me to braodening the universe of this game.

The saving grace of the game for me is when you really try and go through the annoying way of not killing anyone in the game
and come out with 0 livers for the handler and get your very own house. You are granted some sort of clarity,
at least through poetry in the last chat box entry.



## How the project is put together

```
launcher.py            the launcher, this is the file you run
src/game.py        the whole game
media/             every asset - models, textures, audio, fonts, the DOOM map,
                   the sprites, the guns
README.md          this file lol
GAME_GUIDE.md      how to play it and how the code is laid out
REFERENCES.md      every asset that is not mine, with the author and the licence
```

nothing in the game has a file path typed into it. The project walks itself once when it starts and builds a name to path dictionary, so
`find_asset('villagerMODEL.obj')` finds that file wherever it happens to be
sitting. That is why i could move every asset into the media folder without
changing a single filename in the code. Three folders are found by their folder
name instead and must not be renamed: village, DOOM_E1M1 and sprites, more on this in the game_guide

Also a missing file is never a crash. Every loader prints `!!` and carries on, so
the game always starts and i can SEE what is missing instead of reading a
traceback.

GAME_GUIDE.md goes through all of this properly.


## Problems i had, and what fixed them

These are the ones that actually cost me time. Every single one of them i found by
playing the game and noticing something was wrong.

**COORDINATE MAPPING, AND COLLIDERS
it's just physical work that in a real game engine would never come up, or atleast wouldn't be as difficult as it was here,
i don't really know what to say, I had to for the most part just go around with my "P" button, which was great, but very time consuming,
but i didn't really know what other way to place everything in its right place and right scale.

**The throne room ran at about 6 fps.** The model is only 24 000 triangles with I NOTE THIS IN THE COMMENTS BUT I USED AI FOR THIS, BECAUSE IT WAS SO CONFUSING
one material and a tiny texture, so it could not be a drawing cost. It was
`collider='mesh'`, which in Panda3D makes one collision polygon per triangle all
in one node with no tree over them, so every ray the player fires every frame was
being tested against all 24 000 of them. I bake a grid instead now. 
1300 triangles instead of 24 000 and it still keeps the step in the middle of the floor.

**The village houses were impossible to find in the mesh.** I tried to find them
in the geometry and gave up. What worked was walking around the village in game,
standing in front of each house, and pressing P to print my own coordinates - then
I just make them into the door. Door 4 took me two goes. Everything placed in this
game is a number i stood on and printed, not a number i guessed.

**The game got slower the longer i played.** Every gunshot and beep goes through
ursina's `ursfx()`, which makes an Audio object - and an Audio is an Entity - and
it never destroys it, it only stops it. Entities live in `scene.entities` and the
engine walks that list every single frame. So every shot i fired left a dead
object in the frame loop forever. I Wrapped it so the object gets destroyed once the
sound has finished, but this for a while I had no idea about, and pain stackingly annoyed me.

**My hands changed colour in the distance.** I was sure this was the fog and i
blamed the fog twice. It is not possible for the fog to do it, the viewmodel is
drawn in its own pass. It was a 60 metre transparent sphere sitting
on the player's head wearing the sky texture, drawn in the transparent bin AFTER
everything solid - so the half of the sphere between the camera and my hands was
being painted over them. It faded in the further you got from the desk which is
exactly why it looked like distance.

This was because i didn't delete most of the old features like the fog, and they came to annoy me later :()

**Ursina changing between versions.** `color.rgb()` takes 0-255 on some versions
and 0-1 on others and it does not warn you, it just clamps, so every colour came
out white. Everything goes through one `RGB()` helper now that works on both.
`load_texture()`'s second argument is also named differently between versions,
which raised a TypeError and returned None, so sprites were invisible while the
animation code happily kept counting frames. But this wasn't that bad because i got an output constantly
that there was a newer update so eventually I figured it out. ONLY THE PROBLEM WAS,
THAT ONLY THE OLDER MODEL ENDED UP WORKING BECAUSE 

some other parts of my code like the weapons were pulled from code which was written on older Ursina, so I ended up with going
with the older ursina ot not have to worry about the colour no more.

**The village was too slow.** 
The world geometry was six meshes that each spanned the entire map, so their bounding boxes
were always on screen and nothing could ever be culled - cut into 12 metre columns
the culling finally has something to throw away. AMAZING. The wall colliders are 996 boxes
and only the 40 nearest me are switched on. And vsync off, because with vsync on a
frame that misses 60Hz by a millisecond waits for the next refresh, so you do not
get 55 fps, you get 30.

**Scaling.** Models come in completely different units, one tree was 1100 units
tall and a bench was 1.0. There is not a single typed in scale in the game. It
reads the model's real bounding box and scales it to a height in metres ROUGHLY.


## What i would do next

Make the livers spendable. The game prices a life at 400, I would make a full
stock market system, like in Cruelty Squad, where you can based on what you have done in the game
see how the market moves and can buy more cool weapons.
 
Also Footsteps, ambience and some kind of village drone would do
more for the feeling than any more visual work.

A save, function that's REALLY MISSING.

SCRAP THE DOOM LEVEL, and make a more stylistically consistent game, even though the game is supposed to be
style wise chaotic and barely intelligable, but the gun system and enemy ai should be completely revamped

I WISH TO CONTINUE THIS PROJECT IN GODOT game engine , AND SEE HOW FAR I CAN TAKE IT!!!!
AND ALSO NEVER NEVER NEVER USE URSINA AGAIN.
It was a nice starting point, but i feel likeso many of my limitations and probems came from the lack of tutorials
or to be fair my lack of skills.

## References

Everything in this project that i did not make myself - models, sounds, fonts,
code i borrowed - is listed in REFERENCES.md with the author, the licence and a
link. The big ones are mandaw2014's Sandbox for the weapon models and sounds, the
soviet village model, the DOOM map and DOOM's own enemy chasing algorithm.


## Licence

see LICENSE file. That covers my code. The assets are not mine to licence and they
keep the licences of whoever made them, which are all written down in
REFERENCES.md.
