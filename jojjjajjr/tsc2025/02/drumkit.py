from coldtype import *

midi = MidiTimeline(ººsiblingºº("media/tsc_beat1.mid"))
wav = ººsiblingºº("media/tsc_beat1_simple.wav")

rs1 = random_series(start=1, end=2)

@animation(tl=midi, bg=1, audio=wav)
def drumkit(f:Frame):
    kick = midi.ki([20, 36])
    alt_kick = midi.ki(36)
    snare = midi.ki([25, 41])
    alt_snare = midi.ki(41)
    hat = midi.ki(54)

    bar = midi.ki(58).index()

    #s = Scaffold(f.a.r.inset(60)).numeric_grid(1, 3, start_bottom=False)
    #return s.view().f(0)

    return (P(
        StSt("HAT", "PolymathV", 100, wght=hat.adsr(), ital=hat.adsr(rng=(1, 0))),
        StSt("SNARE", "PolymathV"
            , fontSize=snare.adsr(rng=(150, 150))
            , wght=snare.adsr(rng=(0, 1))
            , opsz=snare.adsr(rng=(1, 0))
            , rotate=alt_snare.adsr(rng=(0, 30))),
        StSt("KICK", "ObviouslyV", 300
            , wdth=kick.adsr(rng=(0, 0.15))
            , wght=kick.adsr()
            , ss01=alt_kick.on()))
        .stack(10)
        .xalign(f.a.r)
        .align(f.a.r)
        .insert(0, StSt(f"{bar+1}", "PolymathV", 1100, wght=1, tnum=1, opsz=1)
            .align(f.a.r)
            .f(bw(0, 0.1))))