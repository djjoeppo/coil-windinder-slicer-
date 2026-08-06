# ESP32 Serial Feedback Protocol - Handleiding voor Ontwikkelaars

Beste collega! Om ervoor te zorgen dat de live posities (X, Y, Z, A) en de Z-kracht (in kg) van de wikkelmachine real-time getoond worden op het digitale dashboard (DRO) van de Python applicatie én **automatisch gefilterd** worden zodat ze niet het G-code terminalvenster vervuilen, hebben we een speciaal filter ingebouwd.

Hieronder vind je exact de specificaties waaraan de serieële output (feedback) vanuit de ESP32 moet voldoen.

---

## Aanbevolen Protocol (Sleutel-Waarde Formaat)

Dit is het makkelijkst te implementeren in C/C++ (Arduino/ESP-IDF). Zolang een verzonden regel de letters **X**, **Y**, **Z**, **A** of **W** (of **FORCE**) bevat met een getal erachter, wordt de regel onderschept, uitgelezen in de GUI en verborgen voor de terminal.

### C/C++ (ESP32) Code Voorbeeld:
Je kunt eenvoudig `Serial.printf` gebruiken om de posities periodiek te verzenden (bijvoorbeeld elke 50ms of 100ms):

```cpp
// ESP32 Firmware Voorbeeld
float x_pos = 12.34;   // Breedte (travees) in mm
float y_pos = 5.67;    // Nozzle afstand in mm
float z_pos = 1.20;    // Draadspanning/druk in mm
float a_pos = 90.0;    // Rotatie van de spoel in graden (of aantal turns * 360)
float z_force = 2.45;  // Loadcell kracht/gewicht in kg

// Stuur de data over Serial:
Serial.printf("X:%.2f Y:%.2f Z:%.2f A:%.1f W:%.2f\n", x_pos, y_pos, z_pos, a_pos, z_force);
```

### Belangrijke regels voor de ESP32 output:
1. **Sleutels (X, Y, Z, A, W):** Gebruik hoofdletters (hoewel de parser ook kleine letters aankan, zijn hoofdletters het meest robuust).
2. **De Z-Kracht (Loadcell):** De kracht kan worden aangeduid met de letter **W** (Weight), **KG**, of **FORCE** (bijv. `W:2.45` of `FORCE:2.45`).
3. **Scheidingsteken:** Een simpele dubbele punt of spatie is perfect.
4. **Einde van de regel:** Sluit elke verzonden regel af met een newline (`\n` of `println`).

---

## Alternatief Protocol (GRBL Status Rapportage Formaat)

Mocht je firmware gebaseerd zijn op of compatibel zijn met GRBL, dan ondersteunt de parser ook de standaard `MPos:` statusrapportages.

### Formaat:
```text
<Idle|MPos:12.340,5.670,1.200,90.000|W:2.45>
```

### C/C++ Code Voorbeeld:
```cpp
Serial.printf("<Run|MPos:%.3f,%.3f,%.3f,%.3f|W:%.2f>\n", x_pos, y_pos, z_pos, a_pos, z_force);
```

---

## Hoe de GUI dit verwerkt (Achter de schermen)
Wanneer de Python app een regel ontvangt via de USB-seriële poort:
1. De app controleert of de regel voldoet aan de bovenstaande patronen (bijv. bevat `X:`, `Y:`, `Z:`, `A:` of `MPos:`).
2. **Indien JA:** De app haalt de getallen eruit, update direct de 5 grote groene digitale displays bovenaan de interface, en **stopt met het printen in de terminal**. Hierdoor blijft de G-code monitor prachtig schoon en overzichtelijk!
3. **Indien NEE:** (Bijvoorbeeld bij `ok` of foutmeldingen): De app print de regel gewoon in het groene terminalvenster als normale log.
