# Test clip prompts (for any text-to-video model)

Goal: synthetic home-camera clips where we already know the right answer, to score `brain/label_test.py`.
Name each file by its answer: `anxious_1.mp4`, `calm_2.mp4`, ...

## How these prompts are built
- **Only the behavior changes.** Same room, same camera, same dog in every clip, so Claude is judged on the dog's body language, not the scenery.
- **Behavior as a timeline** (0-3 s, 3-7 s, 7-10 s). Video models follow beats better than a single description, and our classifier compares frames taken seconds apart.
- **Name the body cues** the classifier looks for (ears, tail, panting, gaze). Vague words like "sad dog" come out as a random dog.
- **A negative prompt** blocks the usual AI-video tells: cuts, camera moves, people, cartoon style.

---

## 1. Paste before every prompt (scene)
```
Static home security camera footage. Wide-angle lens mounted high in the corner of a small living room,
looking down at a slight angle. Slightly grainy, compressed, realistic, natural daylight from a window.
A white timestamp in the top-left corner. Grey sofa on the left, a rug in the middle, a closed wooden
front door on the right. One medium-sized tan mixed-breed dog with a red collar. No people.
One continuous 10-second shot. The camera never moves.
```

## 2. Negative prompt (if the model has a field for it; otherwise add "Avoid: ..." at the end)
```
camera movement, zoom, pan, cuts, multiple shots, people, hands, humans' voices, cartoon, anime, 3D render,
cinematic lighting, shallow depth of field, slow motion, text other than the timestamp, more than one dog
```

## 3. Behavior prompts (append one to the scene)

| File | Behavior prompt |
|---|---|
| `calm_1` | 0-10 s: the dog lies on the rug, awake, head resting on its front paws, eyes open, blinking slowly. Body loose, tail still on the floor. It barely moves. Quiet room. |
| `calm_2` | 0-4 s: the dog sits on the rug, relaxed, mouth closed, ears in a neutral position. 4-10 s: it slowly lies down and settles, sighing. Quiet room. |
| `anxious_1` | 0-3 s: the dog paces quickly from the rug to the front door. 3-7 s: it scratches at the door, ears pinned back, tail tucked low, panting hard. 7-10 s: it turns and paces back, then returns to the door. Sound of whining. |
| `anxious_2` | 0-10 s: the dog stands facing the front door and barks repeatedly, jumping up with its front paws on the door between barks, then circling on the spot. Loud continuous barking. |
| `anxious_3` (hard: quiet anxiety) | 0-10 s: the dog stands stiffly in the middle of the room, trembling, tail tucked between its legs, ears flat, lips licking repeatedly, looking around nervously. No barking. |
| `lonely_1` | 0-10 s: the dog lies right next to the front door, awake, chin on the floor, eyes fixed on the door. Low energy. At 6 s it lifts its head, looks at the door, then lays its head back down. Quiet room. |
| `lonely_2` | 0-10 s: the dog sits by the window, staring outside, not moving. Occasionally it glances back at the empty room. One soft whimper. |
| `sleeping_1` | 0-10 s: the dog is curled up asleep on the sofa, eyes closed, breathing slowly and evenly, completely still. Quiet room. |
| `sleeping_2` | 0-10 s: the dog sleeps on its side on the rug, legs stretched out, eyes closed. At 5 s one paw twitches, as if dreaming. Quiet room. |
| `playing_1` | 0-10 s: the dog chases a yellow tennis ball across the rug, pounces on it, does a play bow with its front end low and tail wagging fast, then bats the ball again. Happy, bouncy movement. |
| `playing_2` (hard: looks like pacing) | 0-10 s: the dog does fast, joyful zoomies in a loop around the sofa, mouth open in a relaxed pant, tail up and wagging, ears loose. |
| `not_visible_1` | The same living room with no dog anywhere in view. Nothing moves. |
| `not_visible_2` | The same living room at night: black-and-white infrared night-vision footage, grainy. No dog visible. |

## 4. Night versions (real cameras switch to night vision)
For 2-3 of the clips above, replace "natural daylight from a window" in the scene with:
```
Night time. Black-and-white infrared night-vision footage, grainy, faint glowing eyes on the dog.
```

## 5. Before scoring, check each clip
Watch each one. If the model got the behavior wrong (for example a "lonely" clip where the dog plays), rename it to what it actually shows, or delete it. The file name is the answer key, so it must be true.

## Why the hard cases matter
`anxious_3` (quiet trembling), `playing_2` (zoomies that look like pacing) and `lonely` vs `calm` are where Claude is most likely to be wrong. If it only gets the easy clips right, we don't know much yet.
