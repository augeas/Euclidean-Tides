
from app import TextApp
from machine import Pin
import tidal
import vga2_bold_16x32 as font


def euclid_rhythm(n,k):
    if k > n:
        n,k = k,n
    seq = [[True] for i in range(k)] + [[False] for j in range(n-k)]

    popped = True

    while seq[-1] == seq[-2] and popped: # Are there multiple copies of the same sequence at the end?
        popped = False
        last = seq[-1]

        for item in seq:
            if item == last:
                break # Run out of things to tack the sequence on to...
            else:
                if seq[-1] == last:
                    item += seq.pop()
                    popped = True
                else:
                    break # Run out of copies of the sequence.

    while True:
        for chunk in seq:
            yield from chunk


class EuclidApp(TextApp):
    par_names = [
        'chan A 0', 'chan A 1', 'chan A 2',
        'chan B 0', 'chan B 1', 'chan B 2',
        'tempo'
    ]

    tempo = [75, 125, 250, 375, 500]


    def on_start(self):
        super().on_start()

        self.pins = [
            Pin(18, Pin.OUT),
            Pin(17, Pin.OUT),
            Pin(2, Pin.OUT),
            Pin(5, Pin.OUT)
        ]

        self.buttons.on_press(tidal.JOY_LEFT, self.prev_par)
        self.buttons.on_press(tidal.JOY_RIGHT, self.next_par)

        self.buttons.on_press(tidal.JOY_UP, self.par_up)
        self.buttons.on_press(tidal.JOY_DOWN, self.par_down)

        self.pars = [[4, 9, 25], [9, 25, 49]]
        self.seq = [[[], []], [[], []]]

        self.selected_par = 0
        self.selected_tempo = 2

        self.init_seq(0)
        self.init_seq(1)


    def on_activate(self):
        super().on_activate()
        self.pulse = self.periodic(250, self.seq_step)
        tidal.led_power_on()
        self.update_display()


    def on_deactivate(self):
        super().on_deactivate()
        self.pulse.cancel()
        tidal.led_power_off()


    def init_seq(self, chan):

        pars_1 = self.pars[chan][0:2]
        pars_2 = self.pars[chan][1:]

        if all([par > 0 for par in pars_1 + pars_2]):
            self.seq[chan][0] = euclid_rhythm(*pars_1)
            self.seq[chan][1] = euclid_rhythm(*pars_1)


    def seq_step(self):
        p0 = self.seq[0][0].__next__()
        p1 = self.seq[0][1].__next__()
        p2 = self.seq[1][0].__next__()
        p3 = self.seq[1][1].__next__()

        self.pins[0].value(p0)
        self.pins[1].value(p1)
        self.pins[2].value(p2)
        self.pins[3].value(p3)

        red = 64 * p0 + 128 * p1
        green = 64 * p2 + 128 * p3

        tidal.led[0] = (red, green, 128)
        tidal.led.write()


    def next_par(self):
        self.selected_par = (self.selected_par + 1) % 7
        self.update_display()


    def prev_par(self):
        self.selected_par = (self.selected_par - 1) % 7
        self.update_display()


    def par_up(self):
        self.par_delta(1)


    def par_down(self):
        self.par_delta(-1)


    def par_chan(self):
        if self.selected_par < 6:
            if self.selected_par < 3:
                chan = 0
                par = self.selected_par
            else:
                chan = 1
                par = self.selected_par - 3

            return (par, chan)
        else:
            return (6, None)


    def par_delta(self, delta):
        par, chan = self.par_chan()

        if not chan is None:
            self.pars[chan][par] += delta
            self.init_seq(chan)
        else:
            self.selected_tempo = (self.selected_tempo + delta) % 5
            self.pulse.cancel()
            self.pulse = self.periodic(self.tempo[self.selected_tempo], self.seq_step)

        self.update_display()


    def update_display(self):
        tidal.display.fill(tidal.BLACK)
        tidal.display.text(font, self.par_names[self.selected_par], 0, 20, tidal.WHITE, tidal.BLACK)

        par, chan = self.par_chan()

        if not chan is None:
            tidal.display.text(font, str(self.pars[chan][par]), 0, 50, tidal.WHITE, tidal.BLACK)
        else:
            tidal.display.text(font, str(self.tempo[self.selected_tempo])+'ms', 0, 50, tidal.WHITE, tidal.BLACK)


main = EuclidApp

