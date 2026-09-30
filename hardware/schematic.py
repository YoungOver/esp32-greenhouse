"""Схема электрическая принципиальная: контроллер теплицы на ESP32 (schemdraw) -> schematic.svg"""
import schemdraw
import schemdraw.elements as elm

schemdraw.config(fontsize=12, lw=1.3, font='Arial')
d = schemdraw.Drawing(show=False)


def ic(pins, **kw):
    return elm.Ic(pins=[elm.IcPin(**p) for p in pins], **kw)




def box(p, w, h, txt):
    """прямоугольник датчика слева от точки p (вывод справа, по центру высоты)"""
    x, y = p
    d.add(elm.Line().at((x, y + h / 2)).to((x - w, y + h / 2)))
    d.add(elm.Line().to((x - w, y - h / 2)))
    d.add(elm.Line().to((x, y - h / 2)))
    d.add(elm.Line().to((x, y + h / 2)))
    d.add(elm.Label().at((x - w / 2, y)).label(txt))

# ================= питание (верхняя полоса)
d += (xp1 := ic([dict(name='GND', side='right'), dict(name='+12V', side='right')],
                edgepadW=0.8, pinspacing=1.2, leadlen=0.6, label='XP1', lblloc='top').at((0, 0)))
d += elm.Line().right(0.6).at(xp1['GND'])
d += elm.Ground()
d += elm.Line().right(0.6).at(xp1['+12V'])
d += elm.Fuse().right().label('FU1\n2 А')
d += (vd1 := elm.Diode().right().label('VD1\nSS34'))
d += elm.Dot()
p12 = vd1.end
d += elm.Capacitor(polar=True).down().at(p12).label('C1\n470 мкФ', loc='bot')
d += elm.Ground()
d += elm.Line().up(1.2).at(p12)
d += elm.Vdd().label('+12 В')
d += elm.Line().right(1.4).at(p12)
d += (da1 := ic([dict(name='IN', side='left'), dict(name='OUT', side='right'), dict(name='GND', side='bot')],
                edgepadW=1.6, edgepadH=0.6, label='DA1  MP1584', lblloc='top').anchor('IN'))
d += elm.Ground().at(da1['GND'])
d += elm.Line().right(0.8).at(da1['OUT'])
d += elm.Dot()
p5 = d.here
d += elm.Capacitor().down().at(p5).label('C2\n22 мкФ', loc='bot')
d += elm.Ground()
d += elm.Line().right(1.4).at(p5)
d += (da2 := ic([dict(name='IN', side='left'), dict(name='OUT', side='right'), dict(name='GND', side='bot')],
                edgepadW=1.6, edgepadH=0.6, label='DA2  AMS1117-3.3', lblloc='top').anchor('IN'))
d += elm.Ground().at(da2['GND'])
d += elm.Line().right(0.8).at(da2['OUT'])
d += elm.Dot()
p33 = d.here
d += elm.Capacitor().down().at(p33).label('C3\n10 мкФ', loc='bot')
d += elm.Ground()
d += elm.Line().right(1.0).at(p33)
d += elm.Vdd().label('+3,3 В')

# ================= ESP32 (пины перечислены снизу вверх)
esp = ic([dict(name='GND', side='left', pin='1'), dict(name='IO34', side='left', pin='6'), dict(name='IO4', side='left', pin='26'),
          dict(name='EN', side='left', pin='3'), dict(name='3V3', side='left', pin='2'),
          dict(name='IO26', side='right', pin='11'), dict(name='IO2', side='right', pin='24'),
          dict(name='RXD0', side='right', pin='34'), dict(name='TXD0', side='right', pin='35')],
         edgepadW=2.6, pinspacing=1.6, leadlen=0.8, label='DD1\nESP32-WROOM-32', lblloc='center')
d += esp.at((12, -12))
# левая сторона
d += elm.Line().left(1.0).at(esp['3V3'])
d += elm.Vdd().label('+3,3 В')
d += elm.Line().left(2.8).at(esp['EN'])
d += elm.Dot()
en = d.here
d += elm.Resistor().up().at(en).label('R1 10 к', loc='bot').length(1.4)
d += elm.Vdd().label('+3,3 В')

d += elm.Line().left(4.6).at(esp['IO4'])
d += elm.Dot()
dq = d.here
d += elm.Resistor().up().at(dq).label('R2\n10 к', loc='bot').length(1.3)
d += elm.Vdd().label('+3,3 В')
d += elm.Line().left(2.2).at(dq)
d += elm.Line().left(0.1)
box(d.here, 2.6, 1.0, 'BK1  DHT22')

d += elm.Line().left(1.6).at(esp['IO34'])
d += elm.Dot()
sq = d.here
d += elm.Resistor().down().at(sq).label('R4\n20 к', loc='bot').length(1.3)
d += elm.Ground()
d += elm.Resistor().left().at(sq).label('R3 10 к').length(2.2)
d += elm.Line().left(2.4)
box(d.here, 2.6, 1.0, 'BK2  почва')
d += elm.Line().left(0.8).at(esp['GND'])
d += elm.Ground()

# правая сторона: UART
d += elm.Line().right(2.2).at(esp['TXD0'])
d += (xs1 := ic([dict(name='TX', side='left', slot='1/3'), dict(name='RX', side='left', slot='2/3'), dict(name='GND', side='left', slot='3/3')],
                pinspacing=1.6, edgepadW=0.8, leadlen=0.5, label='XS1  UART', lblloc='top').anchor('RX'))
d += elm.Line().at(esp['RXD0']).to(xs1['TX'])
d += elm.Line().left(0.6).at(xs1['GND'])
d += elm.Ground()
# светодиод
d += elm.Line().right(0.8).at(esp['IO2'])
d += elm.Resistor().right().label('R6 330').length(2.0)
d += elm.LED().right().label('HL1', loc='bot')
d += elm.Line().right(0.4)
d += elm.Ground()
# насос: IO26 -> R5 -> VT1, K1 в коллекторе, VD2 параллельно катушке
d += elm.Line().right(7.5).at(esp['IO26'])
d += elm.Resistor().right().label('R5 1 к').length(2.0)
d += (vt1 := elm.BjtNpn(circle=True).right().anchor('base').label('VT1\nBC547', loc='right', ofst=(0.3, 0)))
d += elm.Ground().at(vt1.emitter)
d += elm.Line().up(0.8).at(vt1.collector)
d += elm.Dot()
kc = d.here
d += elm.Inductor2(loops=3).up().label('K1', loc='bot').length(2.0)
d += elm.Dot()
kt = d.here
d += elm.Line().up(0.6)
d += elm.Vdd().label('+12 В')
d += elm.Line().left(2.4).at(kc)
d += elm.Diode().up().reverse().label('VD2\n1N4148', loc='bot').toy(kt[1])
d += elm.Line().right().tox(kt[0])
# контакты реле
sx, sy = kt[0] + 2.2, kt[1] + 0.6
d += elm.Line().at((kt[0], sy)).right(0) if False else elm.Vdd().at((sx, sy + 0.01)).label('+12 В')
d += elm.Switch(action='close').down().at((sx, sy)).label('K1.1', loc='bot')
d += elm.Motor().down().label('M1\nнасос 12 В', loc='bot')
d += elm.Ground()

d.save('schematic.svg')
print('ok')
