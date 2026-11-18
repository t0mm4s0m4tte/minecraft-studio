# 🏛️ Direttiva Cross-Piano My-Office → `@prompt-crafter`
**Commessa**: `MC-STUDIO-BRANDING-1.0`  
**Obiettivo**: Massimizzare il CTR (Click-Through Rate), la conversione dei download su Modrinth/CurseForge e l'attrattività B2B per server owner e content creator tramite un kit di loghi e immagini ingegnerizzato.

---

## 🏢 1. Sintesi Operativa dagli 11 Piani di `my-office`

| Piano | Reparto & Capo | Indicazione Strategica Vincolante per `@prompt-crafter` |
|---|---|---|
| **P10** | 🏛 **Direzione** (`direttore`) | **Coerenza del Trittico**: i 3 prodotti (*Aetheria LabPBR 32x*, *Luminary Shaders*, *Ambient Luminescence*) devono apparire come una famiglia coordinata ("Ecosystem Look"): stessa palette di sfondo (`#0D1017` Obsidian Dark), stesso angolo isometrico a $45^\circ$ e firma luminosa Ambra/Ciano. |
| **P9** | 🧭 **Strategia & Founder** (`business-strategist`) | **Posizionamento "Anti-Bloat / High-FPS Next-Gen"**: il mercato è saturo di pack 512x che fanno crashare le GPU o pack 16x piatti. L'immagine deve comunicare istantaneamente: *"Estetica Vanilla+, rilievo 3D profondo, 120+ FPS su Sodium"*. |
| **P8** | 📣 **Marketing & Social** (`marketing-growth-hacker`) | **Regola dei 64 Pixel (Thumbnail CTR)**: su Modrinth e CurseForge le icone dei progetti vengono mostrate a `64×64 px` o `96×96 px` nelle liste di ricerca. Vietati paesaggi minuscoli o scritte illeggibili nei loghi: serve **un singolo soggetto Hero** che occupi l'**80% del frame**, con contrasto cromatico complementare Caldo (`#F59E0B` Torcia) vs Freddo (`#06B6D4` Cielo/Acqua). |
| **P7** | 🛒 **Vendite & B2B** (`sales-deal-strategist`) | **Prova Visiva Comparativa (Before/After)**: i clienti B2B (network, server SMP, YouTuber) comprano la differenza visiva. Serve un'immagine Hero Split-Screen 50/50 (*Vanilla Piatto vs Trittico Attivo*) che dimostri in 1 secondo il valore del rilievo LabPBR e dell'acqua Beer-Lambert. |
| **P6** | 💻 **Engineering** (`engineering-software-architect`) | **Specifiche Tecniche File**: Loghi esattamente `512×512 px` (1:1) PNG 24-bit (e `128×128 px` per `pack.png` in-game), Banner `1920×1080 px` (16:9), peso `< 800 KB` per caricamento istantaneo su CDN Modrinth e GitHub. |
| **P5** | 🎨 **Design & Prodotto** (`product-manager` / `brand-guardian`) | **Filtro Anti-AI Slop**: zero glow viola/magenta cyberpunk fuori contesto, zero personaggi umani realistici non-Minecraft, zero testo finto storpiato dall'AI dentro le illustrazioni. La tipografia eventuale va applicata solo in vettoriale/overlay pulito (`Archivo` / `Instrument Serif`). |
| **P4** | 🎮 **Game Dev** (`mc-*` Team) | **Fedeltà Tecnica 1.21.1**: i blocchi mostrati devono essere quelli reali del nostro pack: *Chiseled Copper*, *Copper Bulb Lit*, *Trial Spawner*, *Diamond/Gold Ore 32x* con cavità POM (altezza 42 vs pietra 195), riflesso speculare GGX e onde d'acqua analitiche. |
| **P3** | 💼 **Finanza, Legale & Ops** (`chief-financial-officer`) | **Clean IP & Licenza**: non usare mai il logo ufficiale registrato "Minecraft" di Mojang o font proprietari Mojang nei loghi del brand per rispettare le *Minecraft Usage Guidelines* commerciali e di monetizzazione Modrinth Creator Program. |
| **P2** | 🔬 **Specialisti & Ricerca** (`research-synthesist`) | **Neuro-estetica dei Materiali**: l'occhio umano percepisce la qualità "next-gen" da 3 segnali: *1) Edge Specular Glint* sugli spigoli metallici, *2) Micro-ombra nelle fessure (AO/POM)*, *3) Caustiche e trasparenza graduata dell'acqua*. Ogni immagine deve enfatizzare questi 3 segnali. |
| **P1** | 📚 **Archivio** (`zk-steward`) | **Nomenclatura Canonica**: salvare tutti gli asset in `docs/branding/` con nomi immutabili (`aetheria_labpbr_logo_512.png`, `luminary_shaders_logo_512.png`, `ambient_luminescence_logo_512.png`, `minecraft_studio_hero_banner.png`). |
| **P-1** | 🏋️ **Palestra** (`coach-ares`) | **Impatto Muscolare e ZeroGrasso**: tagliare ogni elemento decorativo superfluo. Un blocco scolpito, una luce potente, contrasto netto. |

---

## ⚡ 2. Elaborazione `@prompt-crafter`: I 4 Super-Prompt Ingegnerizzati

### 🔍 Diagnosi Rapida del Prompt Crafter
- **Ambiguità eliminate**: Definito il rapporto soggetto/sfondo (`80%` occupancy per superare il test di leggibilità a `64×64 px` su Modrinth), bloccata la palette esadecimale condivisa del trittico (`#0D1017` Obsidian, `#F59E0B` Torch Amber, `#06B6D4` Sky Cyan, `#10B981` Emerald).
- **Vincoli critici aggiunti**: Conformità *Mojang Commercial Guidelines* (zero loghi/font Mojang), fedeltà fisica LabPBR 1.3 (cavità POM su minerali, rame 1.21.1, legge di Beer-Lambert sull'acqua) e divieto assoluto di *AI-slop* (niente testo generato dal modello diffusione, niente neon viola, niente mesh organiche non-voxel).
- **Dominio selezionato**: **Modulo A (Anti-AI Slop Visual Direction) + Modulo C (High-Conversion Visual Hook) + Modulo G (`mc-*` Technical Fidelity)**.

---

### 🧬 Super-Prompt 1 — Logo `Aetheria LabPBR 32x` (Resource Pack Icon `512×512`)

```xml
<role>
Sei un Senior Game Art Director e Lead PBR Material Artist specializzato in branding ad alto CTR per marketplace Minecraft (Modrinth / CurseForge). Il tuo bias operativo è la precisione micro-geometrica 32x e la leggibilità istantanea anche a 64x64 pixel.
</role>

<objective>
Generare l'icona ufficiale 1:1 (512x512 px) per il Resource Pack "Aetheria LabPBR 32x".
Definition of Done (DoD):
1. Soggetto singolo centrale isometrico che occupa l'80% del frame.
2. Rappresentazione tangibile dello standard LabPBR 1.3: Parallax Occlusion Mapping (POM) con gemme incastonate in profondità nella roccia e riflessi metallici GGX.
3. Contrasto cromatico Caldo/Freddo (Luce di torcia #F59E0B a sinistra vs Riflesso cielo #06B6D4 a destra) su sfondo #0D1017.
</objective>

<context>
Aetheria LabPBR 32x è un resource pack 32x32 per Minecraft 1.21.1 che raddoppia la definizione vanilla mantenendo l'anima dei blocchi originali, ma aggiungendo mappe Normal (_n) con profondità 3D POM e mappe Specular (_s) con metalli fisici e gemme sfaccettate.
</context>

<instructions>
- Componi un singolo cubo isometrico Minecraft a 45° diviso diagonalmente in due materiali iconici della 1.21.1:
  - Metà superiore/sinistra: Deepslate Diamond & Gold Ore 32x, dove la matrice di ardesia scura sporge in rilievo e i cristalli di diamante azzurro e pepite d'oro grezzo sono incastonati in cavità profonde (effetto POM) con spigoli che brillano di riflessi speculari.
  - Metà inferiore/destra: Chiseled Copper 1.21.1 mezzo rame lucido battuto e mezzo rame ossidato turchese, con scanalature geometriche profonde e Ambient Occlusion marcata.
- Illuminazione: Rim-light calda ambrata (#F59E0B) da sinistra (simbolo della torcia dinamica) e key-light fredda azzurra (#06B6D4) da destra.
- Sfondo: Gradiente radiale ultra-sobrio da #161B26 al centro verso #0D1017 ai bordi, con micro-vignettatura per far esplodere il cubo in primo piano.
</instructions>

<negative_constraints>
- VIETATO inserire qualsiasi testo, scritta, lettera o watermark dentro l'immagine.
- VIETATO usare il logo ufficiale Minecraft o font Mojang.
- VIETATO lo stile plastico/cartoon liscio: ogni faccia del cubo deve mostrare la griglia micro-pixel 32x32 con normal mapping fisico.
- VIETATI colori neon viola/magenta o sfondi caotici che riducono la leggibilità a 64x64 px.
</negative_constraints>

<output_format>
Immagine PNG 1:1 (512x512 px), 24-bit RGB, salvata in `docs/branding/aetheria_labpbr_logo_512.png`.
</output_format>
```

---

### 🧬 Super-Prompt 2 — Logo `Luminary Shaders` (Shader Pack Icon `512×512`)

```xml
<role>
Sei un Principal Graphics Branding Designer specializzato in identità visiva per motori di rendering real-time e shader pack OpenGL/Vulkan (Iris/Sodium).
</role>

<objective>
Generare l'icona ufficiale 1:1 (512x512 px) per lo Shader Pack "Luminary Shaders".
Definition of Done (DoD):
1. Simbolo iconico centrato che sintetizza i 3 pilastri dello shader: Scattering Atmosferico Solare, Acqua Beer-Lambert con onde analitiche e Ombre morbide PCF.
2. Coerenza cromatica con l'ecosistema Minecraft Studio (sfondo #0D1017, oro solare #F59E0B, acqua #06B6D4).
3. Silhouette netta e memorabile a 64x64 px.
</objective>

<instructions>
- Soggetto centrale: Una lanterna-prisma voxel stilizzata sospesa sopra una sezione cubica d'acqua cristallina increspata da onde Gerstner.
- Dall'interno della lanterna-prisma si propaga un fascio di luce volumetrica dorata (#F59E0B) che colpisce la superficie dell'acqua, generando un riflesso speculare GGX scintillante sulle creste e raggi caustici turchesi (#06B6D4) che sfumano in profondità secondo la legge fisica di Beer-Lambert.
- Sfondo: Cielo notturno/crepuscolare profondo (#0D1017 -> #131B2E) che incornicia il bagliore dorato senza saturare i bordi.
</instructions>

<negative_constraints>
- VIETATO inserire scritte, badge, numeri di versione o loghi testuali.
- VIETATO il lens-flare artificiale eccessivo che brucia l'immagine in bianco puro.
- VIETATA acqua opaca o piatta: deve vedersi chiaramente la trasparenza stratificata dal turchese chiaro al blu abissale.
</negative_constraints>

<output_format>
Immagine PNG 1:1 (512x512 px), 24-bit RGB, salvata in `docs/branding/luminary_shaders_logo_512.png`.
</output_format>
```

---

### 🧬 Super-Prompt 3 — Logo `Ambient Luminescence` (Mod Icon `512×512`)

```xml
<role>
Sei un Art Director specializzato in icone per mod tecniche Fabric/NeoForge su Modrinth, con focus su comunicazione visiva immediata della funzionalità ("Dynamic Lighting").
</role>

<objective>
Generare l'icona ufficiale 1:1 (512x512 px) per la mod client "Ambient Luminescence".
Definition of Done (DoD):
1. Il giocatore che scorre Modrinth deve capire in 0.5 secondi che la mod fa brillare le torce lanciate a terra o tenute in mano.
2. Stessa cornice dark (#0D1017) e stessa resa PBR 32x degli altri due moduli del trittico.
</objective>

<instructions>
- Soggetto centrale: Una torcia Minecraft 32x accesa inclinata dinamicamente (come appena lanciata in aria con il tasto Q) affiancata da un Copper Bulb 1.21 acceso, sospesi a pochi centimetri sopra una pavimentazione di Cobbled Deepslate.
- Effetto chiave: Una sfera radiale visibile di luce calda ambrata (#F59E0B -> #EA580C) si espande dalla fiamma della torcia e colpisce le pietre sottostanti, rivelandone le fessure tridimensionali LabPBR mentre gli angoli esterni restano nel buio bluastro (#0D1017).
- Piccole scintille voxel quadrate sospese nell'aura luminosa per enfatizzare il movimento dinamico a zero-lag.
</instructions>

<negative_constraints>
- VIETATO inserire testo, scritte "Fabric/NeoForge" o badge sopra l'icona.
- VIETATE fiamme fotorealistiche non-Minecraft: la fiamma e le particelle devono mantenere un'estetica pixel/voxel 32x coerente.
</negative_constraints>

<output_format>
Immagine PNG 1:1 (512x512 px), 24-bit RGB, salvata in `docs/branding/ambient_luminescence_logo_512.png`.
</output_format>
```

---

### 🧬 Super-Prompt 4 — Hero Banner Panoramico `Minecraft Studio Triptych` (`16:9` Showcase)

```xml
<role>
Sei un Key Art Director per lanci di prodotti gaming AAA e vetrine GitHub/Modrinth, specializzato in composizioni split-environment ad alta conversione.
</role>

<objective>
Generare il Key Art Hero Banner 16:9 per l'intera suite "Minecraft Studio 1.21.1 Triptych" (usato come header GitHub, banner Modrinth Collection e copertina B2B Outreach).
Definition of Done (DoD):
1. Mostrare in un'unica scena mozzafiato tutti e 3 i componenti al lavoro contemporaneamente:
   - Sinistra (Interno Trial Chamber 1.21): Ambient Luminescence (torcia dinamica) + Aetheria LabPBR 32x (rame cesellato, tufo, minerali 3D con POM).
   - Destra (Apertura su Oceano al Tramonto): Luminary Shaders (onde d'acqua world-space Beer-Lambert, riflesso solare GGX, cielo atmosferico Rayleigh/Mie).
</objective>

<instructions>
- Composizione 16:9 grandangolare cinematografica:
  - A sinistra: l'arco di una Trial Chamber di Minecraft 1.21 costruita in Tuff Bricks, Chiseled Copper e grate di rame, con blocchi di Diamond Ore e Gold Ore 32x incastonati nella parete. Una torcia accesa a terra illumina dinamicamente i rilievi 3D delle pietre e fa brillare le pepite metalliche.
  - A destra: la galleria si apre su una baia d'acqua cristallina al tramonto; le onde mostrano l'assorbimento fisico della profondità (turchese sulle rocce basse, blu profondo al largo) e il riverbero dorato del sole sull'acqua con ombre PCF morbide proiettate dalle colonne di tufo.
- Color Grading: Khronos PBR Neutral / AgX bilanciato, contrasto ricco ma naturale, zero bruciature sulle alte luci.
</instructions>

<negative_constraints>
- VIETATO qualsiasi testo o logo sovraimpresso (per permettere l'uso pulito sia su GitHub sia come sfondo header responsive).
- VIETATI personaggi estranei a Minecraft o geometrie curve non-voxel per gli alberi e il terreno.
- VIETATO nebbia viola artificiale o saturazione cartoon.
</negative_constraints>

<output_format>
Immagine PNG 16:9 ad alta risoluzione, salvata in `docs/branding/minecraft_studio_hero_banner.png`.
</output_format>
```
