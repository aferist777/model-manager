"""Dark theme tokens + global QSS. Ported from the HTML mockup palette
(charcoal tinted toward the coral accent hue)."""

C = {
    "bg":        "#1a1613",
    "surface":   "#231f1b",
    "surface2":  "#2b2722",
    "line":      "#3a352e",
    "line_soft": "#322e28",
    "ink":       "#f4efe9",
    "ink_dim":   "#c3bbb0",
    "ink_mute":  "#918a7f",
    "accent":    "#e5825f",
    "accent_ink":"#2a1712",
    "accent_dim":"#3a2820",
    "good":      "#79cf9a",
    "warn":      "#e0c56e",
}

# Reusable avatar gradient stops (also used by avatar.py)
PALETTES = [
    ("#e8825f", "#b4553a"),
    ("#7aa2f7", "#5a6fd0"),
    ("#7ad196", "#4f9e6b"),
    ("#e0c56e", "#b89a4a"),
    ("#c98fe0", "#9a5fc0"),
    ("#79c6d1", "#4f9aae"),
]


def qss() -> str:
    return f"""
    * {{
        font-family: "Segoe UI", system-ui, sans-serif;
        color: {C['ink']};
        font-size: 12px;
    }}
    QMainWindow, QWidget#Root {{ background: {C['bg']}; }}

    /* ---- panes ---- */
    QWidget#Pane {{ background: {C['bg']}; }}
    QWidget#PaneHead {{
        background: {C['bg']};
        border-bottom: 1px solid {C['line_soft']};
    }}
    QLabel#PaneTitle {{ font-size: 12px; font-weight: 500; letter-spacing: 0.3px; }}
    QLabel#PaneCount, QLabel#Muted {{ color: {C['ink_mute']}; font-size: 11px; }}

    QSplitter::handle {{ background: {C['line_soft']}; }}
    QSplitter::handle:horizontal {{ width: 5px; }}   /* wide enough to actually grab */
    QSplitter::handle:horizontal:hover {{ background: {C['accent']}; }}

    /* ---- scrollbars ---- */
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {C['line']}; border-radius: 5px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: {C['line_soft']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    /* ---- buttons ---- */
    QPushButton {{
        background: transparent;
        color: {C['ink_dim']};
        border: 1px solid {C['line']};
        border-radius: 7px;
        padding: 7px 13px;
        font-weight: 600;
        font-size: 12px;
    }}
    QPushButton:hover {{ color: {C['ink']}; background: {C['surface']}; }}
    QPushButton#IconBtn {{ padding: 0; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; font-size: 14px; }}
    QPushButton#AddBtn {{
        color: {C['accent_ink']}; background: {C['accent']}; border: none; font-weight: 700;
    }}
    QPushButton#AddBtn:hover {{ background: #ef8f6d; }}
    QPushButton#Primary {{ color: {C['accent_ink']}; background: {C['accent']}; border: none; }}
    QPushButton#Primary:hover {{ background: #ef8f6d; }}

    /* ---- disabled state (must read as "locked", e.g. while generating) ---- */
    QPushButton:disabled {{ color: {C['line']}; border-color: {C['line_soft']}; background: transparent; }}
    QPushButton#Primary:disabled, QPushButton#AddBtn:disabled {{
        background: {C['accent_dim']}; color: {C['ink_mute']}; border: none;
    }}
    QPushButton#RndBtn:disabled {{ color: {C['line']}; border: 1px solid {C['line_soft']}; background: transparent; }}
    QPushButton#PillL:disabled, QPushButton#PillR:disabled {{
        color: {C['line']}; border-color: {C['line_soft']}; background: transparent;
    }}
    QPushButton#PillL:checked:disabled, QPushButton#PillR:checked:disabled {{
        background: {C['accent_dim']}; color: {C['ink_mute']}; border-color: {C['accent_dim']};
    }}
    QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled {{
        color: {C['ink_mute']}; border-color: {C['line_soft']}; background: {C['bg']};
    }}

    /* ---- tabs ---- */
    QPushButton#Tab {{
        border: none; background: transparent; color: {C['ink_mute']};
        padding: 6px 12px; border-radius: 6px; font-weight: 500; font-size: 12px;
    }}
    QPushButton#Tab:hover {{ color: {C['ink_dim']}; background: {C['surface']}; }}
    QPushButton#Tab:checked {{ color: {C['ink']}; background: {C['surface2']}; }}

    /* ---- workspace ---- */
    QLabel#WsTitle {{ font-size: 15px; font-weight: 600; }}
    QLabel#WsNiche {{ color: {C['ink_mute']}; font-size: 12px; }}
    QLabel#SpecHead {{ color: {C['ink_mute']}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
    QLabel#SpecKey {{ color: {C['ink_mute']}; font-size: 12px; }}
    QLabel#SpecVal {{ color: {C['ink_dim']}; font-size: 12px; font-weight: 600; }}
    QWidget#SpecRow {{ border-bottom: 1px solid {C['line_soft']}; }}

    /* ---- model card ---- */
    QFrame#ModelCard {{ border: 1px solid transparent; border-radius: 11px; }}
    QFrame#ModelCard:hover {{ background: {C['surface']}; }}
    QFrame#ModelCard[selected="true"] {{ background: {C['surface']}; border: 1px solid {C['line']}; }}
    QLabel#ModelName {{ font-weight: 600; font-size: 13px; }}
    QPushButton#CardDel {{
        padding: 0; border: none; border-radius: 10px; background: transparent;
        color: {C['ink_mute']}; font-size: 15px; font-weight: 700;
    }}
    QPushButton#CardDel:hover {{ background: {C['accent_dim']}; color: {C['accent']}; }}
    QLabel#Pill {{ font-size: 10px; font-weight: 600; padding: 1px 7px; border-radius: 10px; }}

    /* ---- instagram / refs ---- */
    QWidget#IgWebWrap {{ border: 1px solid {C['line']}; border-radius: 11px; }}
    QLabel#RefsHead {{ color: {C['ink_mute']}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
    QLineEdit {{
        background: {C['surface']}; border: 1px solid {C['line']}; border-radius: 7px;
        padding: 7px 10px; color: {C['ink']}; font-size: 12px;
    }}
    QLineEdit:focus {{ border: 1px solid {C['accent']}; }}
    QFrame#RefCard {{ border: 1px solid {C['line_soft']}; border-radius: 10px; }}
    QFrame#RefCard:hover {{ background: {C['surface']}; border: 1px solid {C['line']}; }}
    QLabel#RefTitle {{ font-size: 12px; font-weight: 500; }}
    QLabel#RefNote {{ color: {C['ink_mute']}; font-size: 11px; }}

    /* ---- content tiles ---- */
    QPushButton#Tile {{
        border: 1px dashed {C['line']}; border-radius: 11px; color: {C['ink_mute']};
        font-weight: 500; padding: 26px 10px;
    }}
    QPushButton#Tile:hover {{ border: 1px dashed {C['accent']}; color: {C['ink_dim']}; }}

    /* ---- dialog ---- */
    QDialog {{ background: {C['surface']}; }}
    QDialog QLabel#DlgTitle {{ font-size: 14px; font-weight: 600; }}
    QDialog QLabel#FieldLabel {{ color: {C['ink_dim']}; font-size: 11px; font-weight: 600; }}
    QFrame#StepDot {{ border-radius: 2px; background: {C['line']}; }}
    QFrame#StepDot[done="true"] {{ background: {C['accent']}; }}

    /* chips (toggle buttons) */
    QPushButton#Chip {{
        border: 1px solid {C['line']}; border-radius: 14px; padding: 5px 12px;
        color: {C['ink_dim']}; font-weight: 500; font-size: 12px;
    }}
    QPushButton#Chip:hover {{ color: {C['ink']}; border: 1px solid {C['line_soft']}; }}
    QPushButton#Chip:checked {{ background: {C['accent_dim']}; border: 1px solid {C['accent']}; color: {C['ink']}; }}

    QSlider::groove:horizontal {{ height: 4px; background: {C['line']}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {C['accent']}; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px; }}
    QSlider::sub-page:horizontal {{ background: {C['accent']}; border-radius: 2px; }}

    /* ---- menu bar (thin top strip) ---- */
    QMenuBar {{ background: {C['bg']}; color: {C['ink_dim']}; border-bottom: 1px solid {C['line_soft']}; padding: 2px 6px; }}
    QMenuBar::item {{ background: transparent; padding: 4px 11px; border-radius: 5px; font-size: 12px; }}
    QMenuBar::item:selected {{ background: {C['surface2']}; color: {C['ink']}; }}
    QMenuBar::item:pressed {{ background: {C['surface2']}; }}
    QMenu {{ background: {C['surface2']}; border: 1px solid {C['line']}; border-radius: 8px; padding: 6px; }}
    QMenu::item {{ padding: 7px 22px 7px 14px; border-radius: 5px; color: {C['ink_dim']}; }}
    QMenu::item:selected {{ background: {C['accent_dim']}; color: {C['ink']}; }}
    QMenu::item:disabled {{ color: {C['ink_mute']}; }}
    QMenu::separator {{ height: 1px; background: {C['line_soft']}; margin: 6px 8px; }}

    /* ---- combo boxes / text edits ---- */
    QComboBox {{
        background: {C['surface']}; border: 1px solid {C['line']}; border-radius: 6px;
        padding: 3px 9px; color: {C['ink']}; font-size: 12px;
    }}
    QComboBox:hover {{ border: 1px solid {C['line_soft']}; }}
    QComboBox:focus, QComboBox:on {{ border: 1px solid {C['accent']}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
        border-top: 5px solid {C['ink_mute']}; margin-right: 8px; }}
    QComboBox QAbstractItemView {{
        background: {C['surface2']}; color: {C['ink']}; border: 1px solid {C['line']};
        border-radius: 8px; padding: 4px; outline: none;
        selection-background-color: {C['accent_dim']};
    }}
    QComboBox QAbstractItemView::item {{ min-height: 22px; padding: 2px 8px; border-radius: 5px; }}
    QTextEdit {{
        background: {C['surface']}; border: 1px solid {C['line']}; border-radius: 7px;
        color: {C['ink']}; padding: 8px 10px; font-size: 12px;
    }}
    QTextEdit:focus {{ border: 1px solid {C['accent']}; }}

    /* ---- small inline buttons in generator ---- */
    QPushButton#GBtn {{
        padding: 0; min-width: 24px; max-width: 24px; min-height: 24px; max-height: 24px;
        border: 1px solid {C['line']}; border-radius: 6px; color: {C['ink_mute']}; font-weight: 700; font-size: 11px;
    }}
    QPushButton#GBtn:hover:enabled {{ color: {C['accent']}; border: 1px solid {C['accent']}; }}
    QPushButton#GBtn:disabled {{ color: {C['line']}; border-color: {C['line_soft']}; }}
    QPushButton#RndBtn {{
        padding: 5px 12px; border: 1px solid {C['accent']}; border-radius: 6px;
        color: {C['accent']}; font-weight: 700; background: transparent;
    }}
    QPushButton#RndBtn:hover {{ background: {C['accent_dim']}; }}
    QLabel#OptDesc {{ color: {C['ink_mute']}; font-size: 11px; }}
    QLabel#RequiredLabel {{ color: {C['accent']}; font-weight: 700; font-size: 11px; }}
    QPushButton#PillL, QPushButton#PillR {{
        padding: 4px 16px; border: 1px solid {C['line']}; background: transparent;
        color: {C['ink_mute']}; font-size: 11px; font-weight: 600;
    }}
    QPushButton#PillL {{ border-top-left-radius: 11px; border-bottom-left-radius: 11px;
                         border-top-right-radius: 0; border-bottom-right-radius: 0; border-right: none; }}
    QPushButton#PillR {{ border-top-right-radius: 11px; border-bottom-right-radius: 11px;
                         border-top-left-radius: 0; border-bottom-left-radius: 0; }}
    QPushButton#PillL:checked, QPushButton#PillR:checked {{
        background: {C['accent']}; color: {C['accent_ink']}; border-color: {C['accent']};
    }}
    QPushButton#SlotBtn {{
        border: 1px dashed {C['line']}; border-radius: 8px; background: transparent;
        color: {C['ink_mute']}; font-size: 18px; font-weight: 600;
    }}
    QPushButton#SlotBtn:hover {{ border: 1px dashed {C['accent']}; color: {C['accent']}; }}
    QPushButton#ApplyBtn {{
        padding: 0; border: 1px solid {C['line']}; border-radius: 7px; background: transparent;
        color: {C['line']}; font-weight: 700; font-size: 12px;
    }}
    QPushButton#ApplyBtn:enabled {{ color: {C['accent_ink']}; background: {C['accent']}; border: none; }}
    QPushButton#ApplyBtn:enabled:hover {{ background: #ef8f6d; }}
    QComboBox[req="true"] {{ border: 1px solid {C['accent']}88; }}
    QComboBox[req="true"]:focus, QComboBox[req="true"]:on {{ border: 1px solid {C['accent']}; }}

    /* ---- references select toolbar (clear enabled/disabled state) ---- */
    QPushButton#FavBtn, QPushButton#DelBtn {{
        padding: 0; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px;
        border: 1px solid {C['line_soft']}; border-radius: 7px; background: transparent; font-size: 15px;
    }}
    QPushButton#FavBtn:disabled, QPushButton#DelBtn:disabled {{ color: {C['line']}; border-color: {C['line_soft']}; }}
    QPushButton#FavBtn:enabled {{ color: #f6c454; border: 1px solid #f6c45566; }}
    QPushButton#FavBtn:enabled:hover {{ background: #f6c4541f; }}
    QPushButton#DelBtn:enabled {{ color: {C['accent']}; border: 1px solid {C['accent']}66; }}
    QPushButton#DelBtn:enabled:hover {{ background: {C['accent_dim']}; }}

    /* ---- draft view ---- */
    QLabel#DraftPh {{ color: {C['ink_mute']}; font-size: 12px; }}
    QPushButton#NavBtn {{
        padding: 0; border: 1px solid {C['line_soft']}; border-radius: 7px;
        background: transparent; color: {C['ink_dim']}; font-size: 17px; font-weight: 700;
    }}
    QPushButton#NavBtn:hover {{ border-color: {C['accent']}; color: {C['accent']};
                                background: {C['accent_dim']}; }}
    QLabel#DraftCount {{
        color: {C['ink']}; background: rgba(20,16,13,190); border-radius: 9px;
        padding: 2px 9px; font-size: 11px; font-weight: 600;
    }}

    /* ---- reference photo slots ---- */
    QPushButton#PhotoSlot {{
        border: 1px dashed {C['line']}; border-radius: 10px; background: {C['surface']};
        color: {C['ink_mute']}; font-size: 24px; font-weight: 600; min-height: 120px;
    }}
    QPushButton#PhotoSlot:hover {{ border: 1px dashed {C['accent']}; color: {C['accent']}; }}

    /* ---- casting cards ---- */
    QFrame#CastCard {{
        background: {C['surface']}; border: 1px solid {C['line_soft']}; border-radius: 12px;
    }}
    QFrame#CastCard:hover {{ border: 1px solid {C['line']}; }}
    QFrame#CastCard[chosen="true"] {{ border: 2px solid {C['accent']}; background: {C['accent_dim']}; }}
    QLabel#CardName {{ font-size: 13px; font-weight: 700; }}
    QLabel#CardNiche {{ color: {C['accent']}; font-size: 11px; font-weight: 600; }}
    QLabel#CardShort {{ color: {C['ink_dim']}; font-size: 11px; }}
    QLabel#CardSheet {{
        background: {C['bg']}; border: 1px solid {C['line_soft']}; border-radius: 8px;
        color: {C['ink_mute']}; font-size: 11px;
    }}
    QPushButton#MiniBtn {{
        padding: 4px 11px; border: 1px solid {C['line']}; border-radius: 6px;
        color: {C['ink_dim']}; font-size: 11px; font-weight: 600;
    }}
    QPushButton#MiniBtn:hover:enabled {{ color: {C['ink']}; background: {C['surface2']}; }}
    QPushButton#MiniPrimary {{
        padding: 4px 12px; border: none; border-radius: 6px;
        color: {C['accent_ink']}; background: {C['accent']}; font-size: 11px; font-weight: 700;
    }}
    QPushButton#MiniPrimary:hover:enabled {{ background: #ef8f6d; }}
    QPushButton#MiniPrimary:disabled {{ background: {C['accent_dim']}; color: {C['ink_mute']}; }}
    QTextBrowser#LongText {{
        background: {C['bg']}; border: 1px solid {C['line_soft']}; border-radius: 9px;
        padding: 12px 14px; color: {C['ink_dim']};
    }}
    QSpinBox {{
        background: {C['surface']}; border: 1px solid {C['line']}; border-radius: 6px;
        padding: 5px 8px; color: {C['ink']}; font-size: 12px;
    }}
    QSpinBox:focus {{ border: 1px solid {C['accent']}; }}

    /* ---- generation settings ---- */
    QLabel#PriceLine {{ color: {C['warn']}; font-size: 11px; font-weight: 600; }}
    QLabel#EtaLine {{ color: {C['good']}; font-size: 11px; font-weight: 600; }}
    QLabel#ParamHint {{ color: {C['ink_mute']}; font-size: 10px; }}
    QFrame#Sep {{ color: {C['line_soft']}; max-height: 1px; }}
    QCheckBox {{ color: {C['ink_dim']}; font-size: 11px; spacing: 7px; }}
    QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid {C['line']};
                            border-radius: 4px; background: {C['surface']}; }}
    QCheckBox::indicator:checked {{ background: {C['accent']}; border-color: {C['accent']}; }}
    """
