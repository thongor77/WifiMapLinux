"""Internationalization — tr(key, **kwargs) reads the current language setting."""

from __future__ import annotations
from .settings import get as _get_settings

_T: dict[str, dict[str, str]] = {
    "fr": {
        # ── Menu ─────────────────────────────────────────────────────────────
        "menu_file":                "Fichier",
        "menu_save":                "Sauvegarder le projet…",
        "menu_open":                "Charger un projet…",
        "menu_quit":                "Quitter",
        "menu_export":              "Export",
        "menu_export_png":          "Exporter étage actuel (PNG)…",
        "menu_export_pdf":          "Rapport de couverture (PDF)…",
        "menu_settings":            "Paramètres",
        "menu_language":            "Langue ",
        "menu_language_fr":         "Français",
        "menu_language_en":         "English",
        "menu_help":                "Aide",
        "menu_help_help":           "Aide…",
        "menu_help_about":          "À propos…",

        # ── Window title ──────────────────────────────────────────────────────
        "title_new_project":        "Nouveau projet",

        # ── Language change ───────────────────────────────────────────────────
        "dlg_language_restart_title": "Redémarrage requis",
        "dlg_language_restart_msg":   "La langue sera appliquée au prochain démarrage.",

        # ── Unsaved project ───────────────────────────────────────────────────
        "dlg_unsaved_title":        "Projet non sauvegardé",
        "dlg_unsaved_close_msg":    "Le projet contient des modifications non sauvegardées.\n"
                                    "Voulez-vous le sauvegarder avant de quitter ?",
        "dlg_unsaved_load_msg":     "Le projet actuel a des modifications non sauvegardées.\n"
                                    "Continuer et perdre ces modifications ?",

        # ── Project save / open ───────────────────────────────────────────────
        "dlg_save_title":           "Sauvegarder le projet",
        "dlg_open_title":           "Charger un projet",
        "dlg_project_filter":       "Projet WifiMap (*{ext})",
        "dlg_save_error_title":     "Erreur de sauvegarde",
        "dlg_load_error_title":     "Erreur de chargement",
        "status_project_saved":     "Projet sauvegardé : {path}",
        "status_project_loaded":    "Projet chargé : {path}",

        # ── Alignment ─────────────────────────────────────────────────────────
        "dlg_alignment_title":      "Recalage",
        "msg_no_floor_below":       "Aucun étage inférieur trouvé.",
        "msg_floor_no_plan":        "L'étage « {label} » n'a pas de plan importé.",
        "msg_floor_not_calibrated": "L'étage « {label} » n'est pas encore calibré.",
        "status_alignment_saved":   "Recalage sauvegardé — Δx={ox:.2f} m, Δy={oy:.2f} m · échelle {sx:.0%} × {sy:.0%}",

        # ── Floor selection ───────────────────────────────────────────────────
        "status_scale":             "Échelle : {scale:.1f} px/m — {dist} m",
        "status_plan_no_cal":       "Plan importé — calibration requise",
        "status_no_plan":           "Aucun plan pour cet étage — cliquez 'Importer plan PNG'",

        # ── Import plan ───────────────────────────────────────────────────────
        "dlg_import_title":         "Importer un plan",
        "dlg_image_filter":         "Images (*.png *.jpg *.jpeg *.bmp)",
        "status_plan_imported":     "Plan importé ({w}×{h} px) — cliquez 'Calibrer l'échelle'",

        # ── Calibration ───────────────────────────────────────────────────────
        "status_calibration_start": "Calibration : cliquez 2 points sur le plan",
        "dlg_calibration_title":    "Calibration — distance réelle",
        "dlg_calibration_msg":      "Distance entre les 2 points ({px:.1f} px) en mètres :",
        "status_calibrated":        "Échelle calibrée : {scale:.1f} px/m  ({dist:.2f} m)",

        # ── Wi-Fi measurement ─────────────────────────────────────────────────
        "dlg_measure_title":        "Mesure Wi-Fi",
        "dlg_measure_floor":        "Sur quel étage vous trouvez-vous actuellement ?",
        "status_measure_mode":      "📡  Cliquez sur votre position actuelle sur le plan",
        "status_scan_in_progress":  "Scan Wi-Fi en cours…",
        "dlg_no_network_title":     "Aucun réseau détecté",
        "dlg_no_network_msg":       "Le scan n'a retourné aucun réseau.\n"
                                    "Vérifiez que le Wi-Fi est activé et qu'iw/nmcli est disponible.",
        "status_scan_no_network":   "Scan : aucun réseau détecté",
        "status_measure_cancelled": "Mesure annulée",
        "status_measure_saved":     "Mesure enregistrée — {n} réseau(x) · meilleur signal : {best} dBm",

        # ── Vertical section ──────────────────────────────────────────────────
        "status_section_mode":      "Coupe : cliquez 2 points sur le plan pour définir la ligne de coupe",
        "status_section_updated":   "Coupe mise à jour — {length:.1f} m · {n} étage(s)",

        # ── Virtual AP ────────────────────────────────────────────────────────
        "status_ap_place_mode":     "AP virtuel : cliquez sur la position du point d'accès",
        "status_ap_cancelled":      "Placement AP annulé",
        "status_ap_move_mode":      "Cliquez sur la nouvelle position de l'AP",
        "status_ap_moved":          "AP repositionné",
        "dlg_ap_name_taken_title":  "Nom déjà utilisé",
        "dlg_ap_name_taken_msg":    "Un AP nommé « {label} » existe déjà dans cette maison.\n"
                                    "Choisissez un nom différent.",

        # ── Simulation ────────────────────────────────────────────────────────
        "status_sim_no_scale":      "Simulation : plan non calibré pour cet étage",
        "status_sim_no_ap":         "Simulation : aucun AP virtuel placé (bouton 'Placer AP virtuel')",
        "status_sim_no_ap_cal":     "Simulation : aucun AP sur un étage calibré",
        "status_sim_done":          "Simulation LDPL — {n} AP(s) · {floor}",

        # ── Export ────────────────────────────────────────────────────────────
        "dlg_export_png_title":     "Export PNG",
        "dlg_export_png_save":      "Exporter PNG",
        "dlg_png_filter":           "Images PNG (*.png)",
        "status_png_exported":      "PNG exporté : {path}",
        "dlg_export_png_error":     "Erreur export PNG",
        "dlg_export_pdf_title":     "Export PDF",
        "dlg_export_pdf_save":      "Rapport de couverture",
        "dlg_pdf_filter":           "PDF (*.pdf)",
        "status_pdf_exported":      "PDF exporté : {path}",
        "dlg_export_pdf_error":     "Erreur export PDF",
        "msg_no_floor_selected":    "Aucun étage sélectionné.",
        "msg_no_plan_for_floor":    "Aucun plan importé pour cet étage.",

        # ── Heatmap ───────────────────────────────────────────────────────────
        "status_heatmap_min_pts":   "Heatmap : au moins 2 points de mesure requis",
        "status_heatmap_done":      "Heatmap générée — {n} points",

        # ── Building panel ────────────────────────────────────────────────────
        "panel_buildings_title":    "Maisons",
        "btn_new_building":         "+ Nouvelle maison",
        "btn_new_floor":            "+ Nouvel étage",
        "btn_import_plan":          "Importer plan PNG",
        "btn_calibrate":            "Calibrer l'échelle",
        "btn_measure":              "📡  Mesurer Wi-Fi",
        "btn_place_ap":             "📶  Placer AP virtuel",
        "btn_align":                "↔  Aligner étages",
        "btn_delete_floor":         "✕  Supprimer l'étage",
        "btn_delete_building":      "✕  Supprimer la maison",
        "dlg_delete_floor_title":   "Supprimer l'étage",
        "dlg_delete_floor_msg":     "Supprimer « {label} » et toutes ses mesures ?",
        "dlg_delete_building_title":"Supprimer la maison",
        "dlg_delete_building_msg":  "Supprimer « {name} » et tous ses étages et mesures ?",

        # ── Heatmap controls ──────────────────────────────────────────────────
        "chk_heatmap":              "Heatmap",
        "chk_simulation":           "Simulation",
        "tooltip_simulation":       "Afficher la heatmap simulée (LDPL 3D) à partir des APs virtuels",
        "lbl_network":              "Réseau :",
        "lbl_opacity":              "Opacité :",
        "btn_section":              "Coupe ↕",
        "tooltip_section":          "Tracer une ligne de coupe verticale",
        "combo_best_signal":        "Meilleur signal",
        "chk_view3d":               "Vue 3D",
        "tooltip_view3d":           "Afficher le volume Wi-Fi 3D de la maison (rotation souris, zoom molette)",
        "voxel_empty":              "Activez la Heatmap ou la Simulation puis cochez Vue 3D",

        # ── AP panel ──────────────────────────────────────────────────────────
        "panel_aps_title":          "APs virtuels",
        "btn_edit":                 "Modifier",
        "btn_move":                 "↖  Déplacer",
        "btn_delete_ap":            "✕  Supprimer AP",
        "dlg_delete_ap_title":      "Supprimer AP",
        "dlg_delete_ap_msg":        "Supprimer l'AP « {label} » ?",

        # ── Measurement panel ─────────────────────────────────────────────────
        "panel_measurements_title": "Mesures",
        "tooltip_meas_jump":        "Double-cliquer pour centrer sur le point",
        "btn_delete_measurement":   "✕  Supprimer la mesure",
        "dlg_delete_meas_title":    "Supprimer la mesure",
        "dlg_delete_meas_msg":      "Supprimer ce point de mesure et ses données Wi-Fi ?",
        "measurement_point_label":  "Point {n}",

        # ── Building dialog ───────────────────────────────────────────────────
        "dlg_new_building_title":   "Nouvelle maison",
        "ph_building_name":         "ex: Maison principale",
        "ph_optional":              "optionnel",
        "lbl_name":                 "Nom :",
        "lbl_address":              "Adresse :",

        # ── Floor dialog ──────────────────────────────────────────────────────
        "dlg_new_floor_title":      "Nouvel étage",
        "floor_preset_basement":    "Cave / Sous-sol",
        "floor_preset_ground":      "Rez-de-chaussée",
        "floor_preset_1":           "1er étage",
        "floor_preset_2":           "2e étage",
        "floor_preset_3":           "3e étage",
        "lbl_floor":                "Étage :",
        "lbl_label":                "Libellé :",
        "lbl_ceiling_height":       "Hauteur sous plafond :",
        "lbl_slab_material":        "Matériau dalle :",
        "material_concrete":        "Béton (12 dB) — défaut",
        "material_reinforced":      "Béton armé (18 dB)",
        "material_wood":            "Bois / plancher léger (5 dB)",
        "tooltip_slab_material":    "Atténuation de la dalle (ADR-004 — ITU-R P.1238)\n"
                                    "Utilisée par la simulation Wi-Fi inter-étages.",

        # ── Scan dialog ───────────────────────────────────────────────────────
        "dlg_scan_title":           "Résultats du scan Wi-Fi",
        "scan_summary":             "{n} réseau(x) détecté(s)",
        "col_ssid":                 "SSID",
        "col_bssid":                "BSSID",
        "col_signal":               "Signal (dBm)",
        "col_channel":              "Canal",
        "col_freq":                 "Fréq. (MHz)",
        "ph_scan_label":            "ex: Salon, Chambre 1…",
        "lbl_scan_label":           "Libellé (optionnel) :",
        "btn_save":                 "Enregistrer",

        # ── AP dialog ─────────────────────────────────────────────────────────
        "dlg_ap_title":             "Point d'accès virtuel",
        "lbl_tx_power":             "Puissance TX :",
        "tooltip_tx_power":         "Puissance d'émission typique : 20 dBm (100 mW)",
        "lbl_wifi_band":            "Bande Wi-Fi :",
        "freq_24ghz":               "2.4 GHz — ch 6 (2437 MHz)",
        "freq_5ghz":                "5 GHz — ch 36 (5180 MHz)",
        "freq_6ghz":                "6 GHz — ch 1 (5955 MHz)",

        # ── About dialog ──────────────────────────────────────────────────────
        "about_title":              "À propos de WifiMapLinux",
        "about_description":        "Outil de cartographie Wi-Fi résidentiel multi-étages pour Linux",
        "about_version":            "Version {version}",
        "about_tech_title":         "Technologies",
        "about_tech_body":          "Python 3.11 · PySide6 (Qt6) · NumPy · SQLite · Pillow · vispy",
        "about_github_btn":         "thongor77/WifiMapLinux",

        # ── Help dialog ───────────────────────────────────────────────────────
        "help_title":               "Aide — WifiMapLinux",
        "help_no_content":          "Aucun contenu pour ce sujet.",
        "help_section_desc":        "Description",
        "help_section_steps":       "Étapes",
        "help_section_tips":        "Conseils",
        "help_topic_project":       "Créer un projet",
        "help_topic_calibrate":     "Calibrer l'échelle",
        "help_topic_measure":       "Mesurer le Wi-Fi",
        "help_topic_heatmap":       "Heatmap de couverture",
        "help_topic_simulation":    "Simulation LDPL",
        "help_topic_section":       "Coupe verticale",
        "help_topic_alignment":     "Alignement inter-étages",
        "help_topic_export":        "Export",
        "help_topic_view3d":        "Vue 3D",
    },

    "en": {
        # ── Menu ─────────────────────────────────────────────────────────────
        "menu_file":                "File",
        "menu_save":                "Save project…",
        "menu_open":                "Open project…",
        "menu_quit":                "Quit",
        "menu_export":              "Export",
        "menu_export_png":          "Export current floor (PNG)…",
        "menu_export_pdf":          "Coverage report (PDF)…",
        "menu_settings":            "Settings",
        "menu_language":            "Language ",
        "menu_language_fr":         "Français",
        "menu_language_en":         "English",
        "menu_help":                "Help",
        "menu_help_help":           "Help…",
        "menu_help_about":          "About…",

        # ── Window title ──────────────────────────────────────────────────────
        "title_new_project":        "New project",

        # ── Language change ───────────────────────────────────────────────────
        "dlg_language_restart_title": "Restart required",
        "dlg_language_restart_msg":   "Language will be applied on next startup.",

        # ── Unsaved project ───────────────────────────────────────────────────
        "dlg_unsaved_title":        "Unsaved project",
        "dlg_unsaved_close_msg":    "The project has unsaved changes.\n"
                                    "Do you want to save before quitting?",
        "dlg_unsaved_load_msg":     "The current project has unsaved changes.\n"
                                    "Continue and discard changes?",

        # ── Project save / open ───────────────────────────────────────────────
        "dlg_save_title":           "Save project",
        "dlg_open_title":           "Open project",
        "dlg_project_filter":       "WifiMap project (*{ext})",
        "dlg_save_error_title":     "Save error",
        "dlg_load_error_title":     "Load error",
        "status_project_saved":     "Project saved: {path}",
        "status_project_loaded":    "Project loaded: {path}",

        # ── Alignment ─────────────────────────────────────────────────────────
        "dlg_alignment_title":      "Alignment",
        "msg_no_floor_below":       "No lower floor found.",
        "msg_floor_no_plan":        "Floor '{label}' has no imported plan.",
        "msg_floor_not_calibrated": "Floor '{label}' is not calibrated yet.",
        "status_alignment_saved":   "Alignment saved — Δx={ox:.2f} m, Δy={oy:.2f} m · scale {sx:.0%} × {sy:.0%}",

        # ── Floor selection ───────────────────────────────────────────────────
        "status_scale":             "Scale: {scale:.1f} px/m — {dist} m",
        "status_plan_no_cal":       "Plan imported — calibration required",
        "status_no_plan":           "No plan for this floor — click 'Import PNG plan'",

        # ── Import plan ───────────────────────────────────────────────────────
        "dlg_import_title":         "Import a plan",
        "dlg_image_filter":         "Images (*.png *.jpg *.jpeg *.bmp)",
        "status_plan_imported":     "Plan imported ({w}×{h} px) — click 'Calibrate scale'",

        # ── Calibration ───────────────────────────────────────────────────────
        "status_calibration_start": "Calibration: click 2 points on the plan",
        "dlg_calibration_title":    "Calibration — real distance",
        "dlg_calibration_msg":      "Distance between the 2 points ({px:.1f} px) in metres:",
        "status_calibrated":        "Scale calibrated: {scale:.1f} px/m  ({dist:.2f} m)",

        # ── Wi-Fi measurement ─────────────────────────────────────────────────
        "dlg_measure_title":        "Wi-Fi measurement",
        "dlg_measure_floor":        "Which floor are you currently on?",
        "status_measure_mode":      "📡  Click on your current position on the plan",
        "status_scan_in_progress":  "Wi-Fi scan in progress…",
        "dlg_no_network_title":     "No network detected",
        "dlg_no_network_msg":       "The scan returned no networks.\n"
                                    "Check that Wi-Fi is enabled and that iw/nmcli is available.",
        "status_scan_no_network":   "Scan: no network detected",
        "status_measure_cancelled": "Measurement cancelled",
        "status_measure_saved":     "Measurement saved — {n} network(s) · best signal: {best} dBm",

        # ── Vertical section ──────────────────────────────────────────────────
        "status_section_mode":      "Section: click 2 points on the plan to define the cut line",
        "status_section_updated":   "Section updated — {length:.1f} m · {n} floor(s)",

        # ── Virtual AP ────────────────────────────────────────────────────────
        "status_ap_place_mode":     "Virtual AP: click on the access point position",
        "status_ap_cancelled":      "AP placement cancelled",
        "status_ap_move_mode":      "Click on the new position of the AP",
        "status_ap_moved":          "AP repositioned",
        "dlg_ap_name_taken_title":  "Name already in use",
        "dlg_ap_name_taken_msg":    "An AP named '{label}' already exists in this building.\n"
                                    "Choose a different name.",

        # ── Simulation ────────────────────────────────────────────────────────
        "status_sim_no_scale":      "Simulation: floor plan not calibrated",
        "status_sim_no_ap":         "Simulation: no virtual AP placed (use 'Place virtual AP')",
        "status_sim_no_ap_cal":     "Simulation: no AP on a calibrated floor",
        "status_sim_done":          "LDPL simulation — {n} AP(s) · {floor}",

        # ── Export ────────────────────────────────────────────────────────────
        "dlg_export_png_title":     "PNG Export",
        "dlg_export_png_save":      "Export PNG",
        "dlg_png_filter":           "PNG images (*.png)",
        "status_png_exported":      "PNG exported: {path}",
        "dlg_export_png_error":     "PNG export error",
        "dlg_export_pdf_title":     "PDF Export",
        "dlg_export_pdf_save":      "Coverage report",
        "dlg_pdf_filter":           "PDF (*.pdf)",
        "status_pdf_exported":      "PDF exported: {path}",
        "dlg_export_pdf_error":     "PDF export error",
        "msg_no_floor_selected":    "No floor selected.",
        "msg_no_plan_for_floor":    "No plan imported for this floor.",

        # ── Heatmap ───────────────────────────────────────────────────────────
        "status_heatmap_min_pts":   "Heatmap: at least 2 measurement points required",
        "status_heatmap_done":      "Heatmap generated — {n} points",

        # ── Building panel ────────────────────────────────────────────────────
        "panel_buildings_title":    "Buildings",
        "btn_new_building":         "+ New building",
        "btn_new_floor":            "+ New floor",
        "btn_import_plan":          "Import PNG plan",
        "btn_calibrate":            "Calibrate scale",
        "btn_measure":              "📡  Measure Wi-Fi",
        "btn_place_ap":             "📶  Place virtual AP",
        "btn_align":                "↔  Align floors",
        "btn_delete_floor":         "✕  Delete floor",
        "btn_delete_building":      "✕  Delete building",
        "dlg_delete_floor_title":   "Delete floor",
        "dlg_delete_floor_msg":     "Delete '{label}' and all its measurements?",
        "dlg_delete_building_title":"Delete building",
        "dlg_delete_building_msg":  "Delete '{name}' and all its floors and measurements?",

        # ── Heatmap controls ──────────────────────────────────────────────────
        "chk_heatmap":              "Heatmap",
        "chk_simulation":           "Simulation",
        "tooltip_simulation":       "Show simulated heatmap (LDPL 3D) from virtual APs",
        "lbl_network":              "Network:",
        "lbl_opacity":              "Opacity:",
        "btn_section":              "Section ↕",
        "tooltip_section":          "Draw a vertical cross-section line",
        "combo_best_signal":        "Best signal",
        "chk_view3d":               "3D View",
        "tooltip_view3d":           "Show the 3D Wi-Fi volume of the building (mouse rotation, scroll zoom)",
        "voxel_empty":              "Enable Heatmap or Simulation then tick 3D View",

        # ── AP panel ──────────────────────────────────────────────────────────
        "panel_aps_title":          "Virtual APs",
        "btn_edit":                 "Edit",
        "btn_move":                 "↖  Move",
        "btn_delete_ap":            "✕  Delete AP",
        "dlg_delete_ap_title":      "Delete AP",
        "dlg_delete_ap_msg":        "Delete AP '{label}'?",

        # ── Measurement panel ─────────────────────────────────────────────────
        "panel_measurements_title": "Measurements",
        "tooltip_meas_jump":        "Double-click to centre on point",
        "btn_delete_measurement":   "✕  Delete measurement",
        "dlg_delete_meas_title":    "Delete measurement",
        "dlg_delete_meas_msg":      "Delete this measurement point and its Wi-Fi data?",
        "measurement_point_label":  "Point {n}",

        # ── Building dialog ───────────────────────────────────────────────────
        "dlg_new_building_title":   "New building",
        "ph_building_name":         "e.g.: Main building",
        "ph_optional":              "optional",
        "lbl_name":                 "Name:",
        "lbl_address":              "Address:",

        # ── Floor dialog ──────────────────────────────────────────────────────
        "dlg_new_floor_title":      "New floor",
        "floor_preset_basement":    "Basement",
        "floor_preset_ground":      "Ground floor",
        "floor_preset_1":           "1st floor",
        "floor_preset_2":           "2nd floor",
        "floor_preset_3":           "3rd floor",
        "lbl_floor":                "Floor:",
        "lbl_label":                "Label:",
        "lbl_ceiling_height":       "Ceiling height:",
        "lbl_slab_material":        "Slab material:",
        "material_concrete":        "Concrete (12 dB) — default",
        "material_reinforced":      "Reinforced concrete (18 dB)",
        "material_wood":            "Wood / light floor (5 dB)",
        "tooltip_slab_material":    "Slab attenuation (ADR-004 — ITU-R P.1238)\n"
                                    "Used by the inter-floor Wi-Fi simulation.",

        # ── Scan dialog ───────────────────────────────────────────────────────
        "dlg_scan_title":           "Wi-Fi scan results",
        "scan_summary":             "{n} network(s) detected",
        "col_ssid":                 "SSID",
        "col_bssid":                "BSSID",
        "col_signal":               "Signal (dBm)",
        "col_channel":              "Channel",
        "col_freq":                 "Freq. (MHz)",
        "ph_scan_label":            "e.g.: Living room, Bedroom 1…",
        "lbl_scan_label":           "Label (optional):",
        "btn_save":                 "Save",

        # ── AP dialog ─────────────────────────────────────────────────────────
        "dlg_ap_title":             "Virtual access point",
        "lbl_tx_power":             "TX power:",
        "tooltip_tx_power":         "Typical transmit power: 20 dBm (100 mW)",
        "lbl_wifi_band":            "Wi-Fi band:",
        "freq_24ghz":               "2.4 GHz — ch 6 (2437 MHz)",
        "freq_5ghz":                "5 GHz — ch 36 (5180 MHz)",
        "freq_6ghz":                "6 GHz — ch 1 (5955 MHz)",

        # ── About dialog ──────────────────────────────────────────────────────
        "about_title":              "About WifiMapLinux",
        "about_description":        "Multi-floor residential Wi-Fi mapping tool for Linux",
        "about_version":            "Version {version}",
        "about_tech_title":         "Technologies",
        "about_tech_body":          "Python 3.11 · PySide6 (Qt6) · NumPy · SQLite · Pillow · vispy",
        "about_github_btn":         "thongor77/WifiMapLinux",

        # ── Help dialog ───────────────────────────────────────────────────────
        "help_title":               "Help — WifiMapLinux",
        "help_no_content":          "No content for this topic.",
        "help_section_desc":        "Description",
        "help_section_steps":       "Steps",
        "help_section_tips":        "Tips",
        "help_topic_project":       "Create a project",
        "help_topic_calibrate":     "Calibrate scale",
        "help_topic_measure":       "Measure Wi-Fi",
        "help_topic_heatmap":       "Coverage heatmap",
        "help_topic_simulation":    "LDPL simulation",
        "help_topic_section":       "Vertical section",
        "help_topic_alignment":     "Inter-floor alignment",
        "help_topic_export":        "Export",
        "help_topic_view3d":        "3D View",
    },
}


def tr(key: str, **kwargs) -> str:
    lang = _get_settings().language
    text = _T.get(lang, _T["fr"]).get(key) or _T["fr"].get(key, key)
    return text.format(**kwargs) if kwargs else text
