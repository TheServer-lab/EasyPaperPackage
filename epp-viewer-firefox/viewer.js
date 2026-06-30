const SAMPLE_SOURCE = `%epp=0.3%
@meta title="EPP v0.3 Feature Test"
@meta author="EPP Project"
@header "EPP v0.3 Feature Test"
@footer "Page [page]"

@page 1
@heading "EPP v0.3 — All Features" {bold,align=center}
@text "This document tests every v0.3 feature. Use the arrows to step through pages."
@space
@heading "New in v0.3"
@bullet "Callout boxes — @callout with color=" {type=arrow}
@bullet "Highlighted text — highlight= attribute" {type=arrow}
@bullet "Lined pages — @page N {lined}" {type=arrow}
@bullet "Coloured pages — @page N {color=}" {type=arrow}
@bullet "Page rotation — @page N {rotate=}" {type=arrow}

@newpage

@page 2
@heading "Callout Boxes" {bold}
@callout "Yellow — notes and reminders." {color=yellow}
@callout "Green — success and completed steps." {color=green}
@callout "Blue — informational notes." {color=blue}
@callout "Red — danger and critical errors." {color=red}
@callout "Gray — neutral side notes." {color=gray}
@callout "Purple — tips and hints." {color=purple}

@newpage

@page 3
@heading "Highlighted Text" {bold}
@text "Yellow highlight — default attention marker." {highlight=yellow}
@text "Green highlight — success or passing state." {highlight=green}
@text "Blue highlight — references and links." {highlight=blue}
@text "Pink highlight — drafts or soft warnings." {highlight=pink}
@text "Red highlight — errors or critical values." {highlight=red}
@text "Orange highlight — warnings and cautions." {highlight=orange}
@space
@text "Combined: bold and highlighted." {bold,highlight=yellow}
@text "Combined: centered and highlighted." {align=center,highlight=blue}

@newpage

@page 4 {lined}
@heading "Lined Page" {bold}
@text "This page has notebook-style ruling."
@text "Every line sits on a printed rule."
@text "The red margin line marks the left edge."
@space
@text "Great for notes, journals, or draft pages."
@text "Lined mode is set on the page declaration:"
@code "@page 4 {lined}"

@newpage

@page 5 {color=blue}
@heading "Blue Page" {bold}
@text "This page has a blue paper tint."
@text "Ink colour adjusts automatically for contrast."
@space
@callout "Callouts adapt to the page colour too." {color=blue}

@newpage

@page 6 {color=pink}
@heading "Pink Page" {bold}
@text "A warm pink tint — useful for draft sections."
@bullet "Works with all block types" {type=check}
@bullet "Ink is automatically darkened for contrast" {type=check}

@newpage

@page 7 {color=green}
@heading "Green Page" {bold}
@text "A soft green tint — natural and calm."
@quote "Colour is a power which directly influences the soul."

@newpage

@page 8 {color=yellow}
@heading "Yellow Page" {bold}
@text "A warm yellow tint — like a sticky note."
@callout "Yellow pages draw attention to special sections." {color=yellow}

@newpage

@page 9 {lined,color=yellow}
@heading "Lined + Coloured" {bold}
@text "Lined and coloured can be combined."
@text "This page is yellow with notebook ruling."
@text "Useful for handwritten-feel sections."
@code "@page 9 {lined,color=yellow}"

@newpage

@page 10 {rotate=90}
@heading "Rotated 90 degrees" {bold}
@text "This page is rotated 90 degrees clockwise."
@text "Useful for wide tables or landscape content."

@newpage

@page 11 {rotate=180}
@heading "Rotated 180 degrees" {bold}
@text "This page is upside down."
@text "An unusual layout for special effect pages."

@newpage

@page 12 {rotate=270}
@heading "Rotated 270 degrees" {bold}
@text "This page is rotated 270 degrees."
@text "Equivalent to 90 degrees the other way."
`;

mountViewer(document.getElementById('epp-root'), parseEPP(SAMPLE_SOURCE), { showOpenButton: true });
