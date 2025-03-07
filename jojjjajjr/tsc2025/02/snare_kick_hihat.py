from coldtype import *
from coldtype.midi.controllers import midi_controller_lookup_fn

aspect =  16/9
height = 1080
width = height * aspect
font_size = 150

@animation((width, height), rstate=1)
def scratch(f, rs):
    # Get our midi controller
    controller = midi_controller_lookup_fn(
        "from Max 1",
        cmc=rs.midi,
        channel="1"
    )

    # get font
    font_regex = "Super"
    font = Font.Find(font_regex)


    # assign CC numbers to and define a controller for each param
    low_cc_num = 32
    params = font.variations().keys()
    controllers = {
            param: controller(cc)
            for param, cc in zip(params, range(low_cc_num, low_cc_num+len(params)))
    }

    # print(len(params))

    p = (

        StSt(
            "snare".upper(),
            font_regex,
            font_size,
            **controllers
        )
        .layer(1)
        .stack(50)
        .align(f.a.r, "SW"),

        StSt(
            "kick".upper(),
            font_regex,
            font_size,
            **controllers
        )
        .layer(1)
        .stack(50)
        .align(f.a.r, "S"),

        StSt(
            "hihat".upper(),
            font_regex,
            font_size,
            **controllers
        )
        .layer(1)
        .stack(50)
        .align(f.a.r, "SE")


    )

    return p
