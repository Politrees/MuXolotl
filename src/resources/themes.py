"""Theme definitions for MuXolotl UI
"""

DARK_THEME = {
    "CTk": {
        "fg_color": ["gray95", "gray10"],
    },
    "CTkToplevel": {
        "fg_color": ["gray95", "gray10"],
    },
    "CTkFrame": {
        "corner_radius": 10,
        "border_width": 2,
        "fg_color": ["gray90", "gray13"],
        "border_color": ["gray70", "gray25"],
    },
    "CTkButton": {
        "corner_radius": 8,
        "border_width": 0,
        "fg_color": ["#3B8ED0", "#1F6AA5"],
        "hover_color": ["#36719F", "#144870"],
        "text_color": ["gray98", "gray98"],
    },
    "CTkLabel": {
        "text_color": ["gray10", "gray90"],
    },
    "CTkEntry": {
        "corner_radius": 6,
        "border_width": 2,
        "fg_color": ["gray95", "gray20"],
        "border_color": ["gray70", "gray30"],
        "text_color": ["gray10", "gray90"],
    },
    "CTkOptionMenu": {
        "corner_radius": 6,
        "fg_color": ["#3B8ED0", "#1F6AA5"],
        "button_color": ["#3B8ED0", "#1F6AA5"],
        "button_hover_color": ["#36719F", "#144870"],
    },
    "CTkProgressBar": {
        "corner_radius": 10,
        "border_width": 0,
        "fg_color": ["gray70", "gray30"],
        "progress_color": ["#3B8ED0", "#1F6AA5"],
    },
    "CTkTabview": {
        "corner_radius": 10,
        "fg_color": ["gray90", "gray13"],
        "border_width": 2,
        "border_color": ["gray70", "gray25"],
        "segmented_button_fg_color": ["gray80", "gray20"],
        "segmented_button_selected_color": ["#3B8ED0", "#1F6AA5"],
        "segmented_button_selected_hover_color": ["#36719F", "#144870"],
        "segmented_button_unselected_color": ["gray80", "gray20"],
        "segmented_button_unselected_hover_color": ["gray70", "gray25"],
        "text_color": ["gray10", "gray90"],
        "text_color_disabled": ["gray50", "gray50"],
    },
}

LIGHT_THEME = {
    "CTk": {
        "fg_color": ["gray98", "gray98"],
    },
    "CTkToplevel": {
        "fg_color": ["gray98", "gray98"],
    },
    "CTkFrame": {
        "corner_radius": 10,
        "border_width": 2,
        "fg_color": ["gray95", "gray95"],
        "border_color": ["gray75", "gray75"],
    },
    "CTkButton": {
        "corner_radius": 8,
        "border_width": 0,
        "fg_color": ["#3B8ED0", "#3B8ED0"],
        "hover_color": ["#36719F", "#36719F"],
        "text_color": ["white", "white"],
    },
    "CTkLabel": {
        "text_color": ["gray10", "gray10"],
    },
    "CTkEntry": {
        "corner_radius": 6,
        "border_width": 2,
        "fg_color": ["white", "white"],
        "border_color": ["gray75", "gray75"],
        "text_color": ["gray10", "gray10"],
    },
}
