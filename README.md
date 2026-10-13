# Alexa 5-Button Wall Box

NodeMCU ESP-12E (CP2102) on a "GPIO 1 into 2" breakout board + five 12x12 mm tact switches → Alexa routines → your smart plug and lights.

| Row | Button | Symbol on lid | Pin | Alexa routine |
|---|---|---|---|---|
| Top | 1 | `|` | D5 | Plug **ON** |
| Top | 2 | `O` | D6 | Plug **OFF** |
| Top | 3 | power symbol | D7 | Plug **OFF → wait 10 s → ON** |
| Bottom | 4 | sun | D1 | Lights **ON** |
| Bottom | 5 | moon | D2 | Lights **OFF** |

## 1. Print

- `base.stl` – print open side up. Outside 84.8 x 78.8 x 42 mm. Keyhole slots point up, so the plug row ends up on top. No supports.
- `lid.stl` – print **as exported** (flat face on the bed, button pockets pointing up). No supports.
- PLA/PETG, 0.2 mm layers, 3 walls, 20% infill is plenty.
- Measure your breakout board first: the case assumes 63.5 x 63 mm. If yours differs, edit `BOARD_L / BOARD_W` in `make_case.py` and run `python make_case.py` (needs `pip install manifold3d trimesh numpy`). If the lid is too tight/loose, change `FIT`.

## 2. Wire

Plug the NodeMCU into the breakout board (match the antenna mark). Every pin on the breakout has its own **G / V / S** header group.
Each switch: one leg → that pin's **S**, the **diagonally opposite** leg → that pin's **G**. Female-to-female dupont leads soldered to the switch legs work well.
Leave **V** unused. No resistors needed (the sketch uses internal pull-ups).

```
SW1: D5 ──[ ]── GND
SW2: D6 ──[ ]── GND
SW3: D7 ──[ ]── GND
SW4: D1 ──[ ]── GND
SW5: D2 ──[ ]── GND
```

Push each switch into its square pocket on the underside of the lid from below (legs pointing into the box), put a dab of hot glue on the back, then press the caps on from the front.

The breakout board rests on four corner pads and is located by L-shaped corner fences. Put the edge with the **micro-USB power input** (and power switch, if your board has one) toward the window in the side wall. A dab of hot glue or double-sided tape on the pads holds it.

Power: a 5 V USB phone charger + micro-USB cable.
The window is deliberately wide so it lines up with the micro-USB wherever it sits on that edge; narrow it with `WIN_W` in `make_case.py` if you like.

## 3. Set up the Alexa side (free)

1. Go to **virtualsmarthome.xyz → URL Routine Trigger**, sign in with your Amazon account.
2. Create five triggers, e.g. `Plug On Button`, `Plug Off Button`, `Plug Cycle Button`, `Lights On Button`, `Lights Off Button`. Copy each trigger's URL.
3. In the Alexa app, enable the **Virtual Smart Home** skill and let it discover devices — the five triggers appear as doorbell-type devices.
4. Create five routines (Alexa app → More → Routines → +):
   - *When:* Smart Home → `Plug On Button` → pressed. *Action:* Smart Home → your plug → Power On.
   - *When:* `Plug Off Button` → *Action:* plug → Power Off.
   - *When:* `Plug Cycle Button` → *Actions:* plug Power Off → **Wait** 10 seconds → plug Power On.
   - *When:* `Lights On Button` → *Action:* your lights (or a light group / room) → Power On.
   - *When:* `Lights Off Button` → *Action:* lights → Power Off.
5. Test each URL by opening it in a browser — the routine should run before you've touched any hardware.

## 4. Flash the sketch

1. Arduino IDE → Preferences → Additional Boards URL: `http://arduino.esp8266.com/stable/package_esp8266com_index.json`, then Boards Manager → install **esp8266**.
2. Board: **NodeMCU 1.0 (ESP-12E Module)**. Install the CP2102 USB driver if the COM port doesn't show up.
3. Open `AlexaButtons/AlexaButtons.ino`, fill in your Wi-Fi name/password (2.4 GHz network) and paste the five trigger URLs.
4. Upload. Open Serial Monitor at 115200 to watch it connect.

LED on the board: 2 blinks at boot = ready, 1 blink after a press = sent, 5 fast blinks = failed (check Wi-Fi / URL).
Presses within 2 s of the last one are ignored so a bouncy press can't fire twice.
