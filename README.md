# `ndr_text`

`ndr_text` is a terminal based highly specialised browser for [NDR Text](https://www.ndr.de/fernsehen/videotext/index.html). `ndr_text` uses `BeautifulSoup` to exctact content and display information from the HTML provided by the original application and will break when the original application changes the display model.

The original application [uses](https://www.ndr.de/resources/css/ttx.css) the tius font-family to display some Graphical elements which look odd without it. I didn't put too much time into wether the [.eot](https://www.ndr.de/common/resources/fonts/tius.eot) or the [.otf](https://www.ndr.de/common/resources/fonts/tius.otf) is needed by which terminal emulator to get things looking right, I just put both of them into `/usr/share/fonts/tius` and ran `sudo fc-cache -v` and `gnome-terminal` started displaying the characters like the original application does.

Like the original application the clock in the top right corner is the local system time, not the server time.

The name of this application is a temporary working title.

## Motivation

The original application does not work on my phone since the virtual keyboard is not displayed, but I have a Terminal emulator on my phone, although I still haven't figured out if I need to put the font there and how to do that. Also I wanted to make a simple TUI application for a while before attempting to rewrite the qubes qube manager as a TUI application...

## Plans

- skip over missing pages instead of going back to the start page
- add a way to reload the page list without restarting the application

after that I'm not sure what happens, maybe abandonware, I'm not even sure I'll ever use it for the intended purpose after all
