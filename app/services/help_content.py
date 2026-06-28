"""Help content — topic keys mapped to FR/EN descriptions, steps, and tips."""

from __future__ import annotations
from .settings import get as _get_settings

_CONTENT: dict[str, dict[str, dict]] = {
    "project": {
        "fr": {
            "desc": (
                "Un projet regroupe une maison (Building), ses étages (Floor) et les plans "
                "associés. Toutes les mesures Wi-Fi et les APs virtuels sont attachés à un "
                "étage précis. Le fichier projet (.wifimap) sauvegarde et restaure l'ensemble."
            ),
            "steps": [
                "Fichier → Nouveau projet (ou démarrage : le projet est vide par défaut).",
                "Cliquer 'Nouvelle maison' dans le panneau de gauche pour créer un Building.",
                "Sélectionner la maison dans l'arbre, puis cliquer 'Nouvel étage'.",
                "Pour chaque étage : importer un plan PNG (photo, scan ou dessin).",
                "Calibrer l'échelle de chaque plan avant de mesurer.",
                "Fichier → Sauvegarder le projet pour conserver le travail.",
            ],
            "tips": [
                "Un projet peut contenir plusieurs maisons — utile pour comparer deux bâtiments.",
                "Les étages sont ordonnés par index : -1 (cave), 0 (RDC), 1, 2…",
            ],
        },
        "en": {
            "desc": (
                "A project holds a building, its floors, and associated plans. All Wi-Fi "
                "measurements and virtual APs are attached to a specific floor. The project "
                "file (.wifimap) saves and restores everything."
            ),
            "steps": [
                "File → New project (or launch: project is empty by default).",
                "Click 'New building' in the left panel to create a Building.",
                "Select the building in the tree, then click 'New floor'.",
                "For each floor: import a PNG plan (photo, scan, or drawing).",
                "Calibrate the scale of each plan before measuring.",
                "File → Save project to preserve your work.",
            ],
            "tips": [
                "A project can hold several buildings — useful to compare two properties.",
                "Floors are ordered by index: -1 (basement), 0 (ground), 1, 2…",
            ],
        },
    },

    "calibrate": {
        "fr": {
            "desc": (
                "La calibration établit le ratio pixels/mètre du plan, indispensable pour "
                "que les distances soient réalistes dans la heatmap et la simulation. "
                "Elle se fait en cliquant deux points dont on connaît la distance réelle."
            ),
            "steps": [
                "Sélectionner un étage avec un plan importé.",
                "Cliquer 'Calibrer l'échelle' dans le panneau de gauche.",
                "Cliquer un premier point sur le plan (ex. : un bout de mur).",
                "Cliquer un second point (ex. : l'autre bout du même mur).",
                "Saisir la distance réelle en mètres dans la boîte de dialogue.",
                "Valider — l'échelle (px/m) est calculée et sauvegardée.",
            ],
            "tips": [
                "Choisir deux points éloignés (> 2 m) pour minimiser l'erreur relative.",
                "Une pièce dont vous connaissez la longueur exacte est idéale.",
                "La calibration peut être refaite à tout moment sans perdre les mesures.",
            ],
        },
        "en": {
            "desc": (
                "Calibration establishes the pixels-per-metre ratio of the plan, which is "
                "required for realistic distances in the heatmap and simulation. "
                "It is done by clicking two points whose real-world distance is known."
            ),
            "steps": [
                "Select a floor with an imported plan.",
                "Click 'Calibrate scale' in the left panel.",
                "Click a first point on the plan (e.g. one end of a wall).",
                "Click a second point (e.g. the other end of the same wall).",
                "Enter the real distance in metres in the dialog.",
                "Confirm — the scale (px/m) is computed and saved.",
            ],
            "tips": [
                "Choose two points far apart (> 2 m) to minimise relative error.",
                "A room whose exact length you know is ideal.",
                "Calibration can be redone at any time without losing measurements.",
            ],
        },
    },

    "measure": {
        "fr": {
            "desc": (
                "Un point de mesure enregistre un scan Wi-Fi à une position précise sur le "
                "plan. L'accumulation de points permet de générer la heatmap de couverture "
                "par interpolation IDW."
            ),
            "steps": [
                "Sélectionner un étage calibré.",
                "Cliquer 'Prendre une mesure' — l'application demande de confirmer l'étage.",
                "Cliquer sur le plan à l'endroit exact où vous vous trouvez physiquement.",
                "Le scan Wi-Fi démarre automatiquement (iw / nmcli).",
                "Dans la boîte de dialogue : vérifier les réseaux détectés, ajouter un libellé optionnel, puis Enregistrer.",
                "Le point apparaît dans la liste 'Mesures' et sur le plan.",
            ],
            "tips": [
                "Viser 10–20 points par étage pour une heatmap exploitable.",
                "Bien se placer à l'endroit cliqué (pas dans le couloir si vous cliquez en salon).",
                "Double-cliquer un point dans la liste pour centrer la vue sur lui.",
            ],
        },
        "en": {
            "desc": (
                "A measurement point records a Wi-Fi scan at a specific position on the plan. "
                "Accumulating points generates the coverage heatmap via IDW interpolation."
            ),
            "steps": [
                "Select a calibrated floor.",
                "Click 'Take a measurement' — the app asks you to confirm the floor.",
                "Click on the plan at the exact location where you are physically standing.",
                "The Wi-Fi scan starts automatically (iw / nmcli).",
                "In the dialog: check the detected networks, optionally add a label, then Save.",
                "The point appears in the 'Measurements' list and on the plan.",
            ],
            "tips": [
                "Aim for 10–20 points per floor for a usable heatmap.",
                "Stand exactly where you clicked (not in the hallway if you clicked the living room).",
                "Double-click a point in the list to centre the view on it.",
            ],
        },
    },

    "heatmap": {
        "fr": {
            "desc": (
                "La heatmap de couverture interpole le signal Wi-Fi entre les points de "
                "mesure par la méthode IDW (Inverse Distance Weighting). Elle est affichée "
                "par-dessus le plan de l'étage avec une échelle de couleur −95 → −40 dBm."
            ),
            "steps": [
                "Enregistrer au moins 2 points de mesure sur l'étage.",
                "Cocher 'Heatmap' dans la barre en bas de l'écran.",
                "Utiliser le menu déroulant 'Réseau' pour filtrer par SSID ou afficher le meilleur signal.",
                "Ajuster l'opacité avec le curseur.",
            ],
            "tips": [
                "Rouge foncé = signal fort (> −50 dBm), bleu/violet = signal faible (< −80 dBm).",
                "Avec peu de points (< 5), la heatmap est approximative — les zones sans point sont extrapolées.",
                "La heatmap mesurée et la simulation LDPL sont indépendantes et superposables.",
            ],
        },
        "en": {
            "desc": (
                "The coverage heatmap interpolates Wi-Fi signal between measurement points "
                "using IDW (Inverse Distance Weighting). It is displayed over the floor plan "
                "with a −95 → −40 dBm colour scale."
            ),
            "steps": [
                "Record at least 2 measurement points on the floor.",
                "Tick 'Heatmap' in the bottom bar.",
                "Use the 'Network' dropdown to filter by SSID or show the best signal.",
                "Adjust opacity with the slider.",
            ],
            "tips": [
                "Dark red = strong signal (> −50 dBm), blue/purple = weak signal (< −80 dBm).",
                "With few points (< 5), the heatmap is approximate — areas with no point are extrapolated.",
                "The measured heatmap and LDPL simulation are independent and can be overlaid.",
            ],
        },
    },

    "simulation": {
        "fr": {
            "desc": (
                "La simulation LDPL 3D calcule la couverture théorique de vos APs (réels ou "
                "hypothétiques) en tenant compte de l'atténuation des dalles inter-étages "
                "(modèle ITU-R P.1238). Elle permet d'évaluer l'impact du placement d'un AP "
                "avant de percer des murs ou de tirer des câbles."
            ),
            "steps": [
                "Sélectionner un étage calibré.",
                "Cliquer 'Placer un AP' et cliquer sur le plan à l'emplacement souhaité.",
                "Dans la boîte de dialogue : définir le libellé, la puissance TX et la bande Wi-Fi.",
                "Cocher 'Simulation' dans la barre en bas pour afficher la heatmap simulée.",
                "Ajouter d'autres APs sur d'autres étages pour simuler un réseau complet.",
            ],
            "tips": [
                "La simulation utilise les paramètres d'atténuation de dalle définis à la création de l'étage.",
                "Un AP peut être déplacé après coup via le panneau 'APs virtuels' → bouton 'Déplacer'.",
                "La simulation est recalculée automatiquement à chaque modification d'AP.",
            ],
        },
        "en": {
            "desc": (
                "The LDPL 3D simulation computes the theoretical coverage of your APs (real or "
                "hypothetical) accounting for inter-floor slab attenuation (ITU-R P.1238 model). "
                "It lets you evaluate AP placement impact before drilling walls or running cables."
            ),
            "steps": [
                "Select a calibrated floor.",
                "Click 'Place AP' and click on the plan at the desired location.",
                "In the dialog: set the label, TX power, and Wi-Fi band.",
                "Tick 'Simulation' in the bottom bar to show the simulated heatmap.",
                "Add more APs on other floors to simulate a full network.",
            ],
            "tips": [
                "The simulation uses the slab attenuation set when the floor was created.",
                "An AP can be moved afterwards via the 'Virtual APs' panel → 'Move' button.",
                "The simulation is recomputed automatically on every AP change.",
            ],
        },
    },

    "section": {
        "fr": {
            "desc": (
                "La coupe verticale affiche un profil du signal Wi-Fi sur une ligne que vous "
                "tracez sur le plan. Elle montre l'évolution du signal en fonction de la "
                "distance horizontale, tous étages confondus (mesures + simulation)."
            ),
            "steps": [
                "Cliquer le bouton 'Section ↕' dans la barre en bas.",
                "Cliquer un premier point sur le plan.",
                "Cliquer un second point pour définir la ligne de coupe.",
                "La vue de coupe s'affiche dans le panneau de droite.",
            ],
            "tips": [
                "Tracer la ligne perpendiculairement aux murs pour mieux voir l'atténuation.",
                "La coupe se met à jour automatiquement si vous ajoutez des mesures ou des APs.",
                "La longueur et le nombre de points interpolés sont affichés dans la barre de statut.",
            ],
        },
        "en": {
            "desc": (
                "The vertical section shows a Wi-Fi signal profile along a line you draw on "
                "the plan. It displays signal strength as a function of horizontal distance, "
                "across all floors (measurements + simulation)."
            ),
            "steps": [
                "Click the 'Section ↕' button in the bottom bar.",
                "Click a first point on the plan.",
                "Click a second point to define the section line.",
                "The section view appears in the right panel.",
            ],
            "tips": [
                "Draw the line perpendicular to walls to better visualise attenuation.",
                "The section updates automatically when you add measurements or APs.",
                "The line length and number of interpolated points are shown in the status bar.",
            ],
        },
    },

    "alignment": {
        "fr": {
            "desc": (
                "L'alignement inter-étages superpose visuellement le plan d'un étage sur "
                "celui du dessous pour compenser les différences d'échelle ou de cadrage des "
                "images importées. Il est nécessaire pour que la simulation 3D soit précise."
            ),
            "steps": [
                "Sélectionner un étage (pas le plus bas — l'étage de référence est celui du dessous).",
                "Cliquer 'Aligner sur l'étage inférieur' dans le panneau de gauche.",
                "Dans la fenêtre de recalage : faire glisser le plan courant (semi-transparent) pour le superposer au plan de référence.",
                "Ajuster les facteurs d'échelle X et Y si les plans ont des résolutions différentes.",
                "Valider — le décalage et l'échelle sont sauvegardés.",
            ],
            "tips": [
                "L'alignement est purement visuel ; il ne modifie pas les images d'origine.",
                "Les murs porteurs et les cages d'escalier sont de bons repères d'alignement.",
                "Si les deux plans sont au même endroit mais ont une échelle différente, ajuster l'échelle suffit.",
            ],
        },
        "en": {
            "desc": (
                "Inter-floor alignment visually overlays a floor plan on the one below to "
                "compensate for scale or framing differences between imported images. "
                "It is required for the 3D simulation to be accurate."
            ),
            "steps": [
                "Select a floor (not the lowest — the reference floor is the one below).",
                "Click 'Align on lower floor' in the left panel.",
                "In the alignment window: drag the current plan (semi-transparent) to overlay the reference plan.",
                "Adjust X and Y scale factors if the plans have different resolutions.",
                "Confirm — the offset and scale are saved.",
            ],
            "tips": [
                "Alignment is purely visual; it does not modify the original images.",
                "Load-bearing walls and stairwells are good alignment landmarks.",
                "If both plans are at the same position but differ in scale, adjusting scale alone is enough.",
            ],
        },
    },

    "export": {
        "fr": {
            "desc": (
                "WifiMapLinux peut exporter la vue courante en PNG ou générer un rapport PDF "
                "multi-pages couvrant tous les étages de la maison."
            ),
            "steps": [
                "Pour un PNG : Export → Exporter étage actuel (PNG)…",
                "Choisir un emplacement de sauvegarde.",
                "Pour un PDF : Export → Rapport de couverture (PDF)…",
                "Le PDF inclut automatiquement tous les étages avec le plan et la heatmap active.",
            ],
            "tips": [
                "Le PNG exporte la heatmap active (mesurée ou simulée) superposée au plan.",
                "Le rapport PDF est pratique pour comparer les étages côte à côte.",
                "Si aucune heatmap n'est active, le plan seul est exporté.",
            ],
        },
        "en": {
            "desc": (
                "WifiMapLinux can export the current view as PNG or generate a multi-page "
                "PDF report covering all floors of the building."
            ),
            "steps": [
                "For PNG: Export → Export current floor (PNG)…",
                "Choose a save location.",
                "For PDF: Export → Coverage report (PDF)…",
                "The PDF automatically includes all floors with their plan and active heatmap.",
            ],
            "tips": [
                "The PNG exports the active heatmap (measured or simulated) overlaid on the plan.",
                "The PDF report is useful for comparing floors side by side.",
                "If no heatmap is active, only the plan is exported.",
            ],
        },
    },

    "view3d": {
        "fr": {
            "desc": (
                "La vue 3D affiche le volume Wi-Fi de toute la maison sous forme de voxels "
                "colorés (même palette que la heatmap 2D). Elle est construite en empilant "
                "les grilles IDW ou LDPL de chaque étage et en interpolant verticalement entre "
                "les midpoints d'étage (même algorithme que la coupe verticale V2.2)."
            ),
            "steps": [
                "Activer la heatmap (mesurée) ou la simulation dans la barre en bas.",
                "Cocher 'Vue 3D' dans la barre de contrôle.",
                "La vue 2D (plan + coupe) est remplacée par le volume 3D.",
                "Faire tourner avec la souris (clic gauche), zoomer avec la molette.",
                "Décocher 'Vue 3D' pour revenir à la vue 2D.",
            ],
            "tips": [
                "La source de données (mesurée ou simulée) suit les cases 'Heatmap' et 'Simulation'.",
                "Un étage sans mesure est traversé par interpolation verticale depuis ses voisins.",
                "Le volume n'applique pas les décalages XY inter-étages — utiliser la coupe verticale pour l'analyse précise.",
            ],
        },
        "en": {
            "desc": (
                "The 3D view displays the Wi-Fi volume of the entire building as coloured voxels "
                "(same palette as the 2D heatmap). It is built by stacking the IDW or LDPL grids "
                "of each floor and interpolating vertically between floor midpoints (same algorithm "
                "as the V2.2 vertical section)."
            ),
            "steps": [
                "Enable the heatmap (measured) or the simulation in the bottom bar.",
                "Tick '3D View' in the control bar.",
                "The 2D view (plan + section) is replaced by the 3D volume.",
                "Rotate with the mouse (left click), zoom with the scroll wheel.",
                "Untick '3D View' to return to the 2D view.",
            ],
            "tips": [
                "The data source (measured or simulated) follows the 'Heatmap' and 'Simulation' checkboxes.",
                "A floor without measurements is traversed by vertical interpolation from its neighbours.",
                "The volume does not apply inter-floor XY offsets — use the vertical section for precise analysis.",
            ],
        },
    },
}

_TOPICS_ORDER = [
    "project",
    "calibrate",
    "measure",
    "heatmap",
    "simulation",
    "section",
    "alignment",
    "export",
    "view3d",
]


def get_topics() -> list[str]:
    return _TOPICS_ORDER


def get_help(topic_key: str) -> dict | None:
    lang = _get_settings().language
    content = _CONTENT.get(topic_key)
    if not content:
        return None
    return content.get(lang) or content.get("fr")
