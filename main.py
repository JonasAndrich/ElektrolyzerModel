from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import numpy as np

# Definition von Konstanten als globale Variablen
global F
F = 96485.33289
global R
R = 8.3144598
# Raumtemperatur 25 °C
global Tamb
Tamb = 298.15

'''
Exchange Current Density and alpha values for Cathode and Anode from:
Yigit, T., Selamet, O.F., 2016. Mathematical modeling and dynamic Simulink simu-
lation of high-pressure PEM electrolyzer system. Int. J. Hydrogen Energy 41,
13901e13914. https://doi.org/10.1016/j.ijhydene.2016.06.022.
'''
global I0A
I0A = 2e-07
global ALPPHAA
ALPPHAA = 2
global I0C
I0C = 2e-03
global ALPHAC
ALPHAC = 0.5

app = Dash(__name__)

server = app.server

app.layout = html.Div([
    html.H1(children='Polarisation Curve Simulation of PEM-Elektrolyzer',
            style={'width': '75%', 'margin': 25, 'textAlign': 'center', 'font-family': 'Arial'}),

    html.Div(children='''
        Vielen Dank für die Einladung. Falls Sie sich während des Gesprächs,
        die Zeit vertreiben möchten, finden Sie hier ein rudimentäres interaktives Modell zur 
        Berechnung der Polarisationskurve eines PEM-Elektrolyseurs.
        Ändern sie mithilfe der Slider die Temperature, den Wasser-Gehalt des Nafion 
        oder die Nafion-Membran-Dicke und schauen, 
        wie sich das auf die anteiligen Überspannungen auswirkt.
        ''',
             style={'width': '75%', 'margin': 25, 'textAlign': 'center', 'font-family': 'Arial'}),
    html.Br(),
    dcc.Slider(
        273,
        398,
        step=None,
        marks={
            298: '298K / 25°C',
            323: '313K / 50°C',
            353: '343K / 80°C',
            383: '383K / 100°C'
        },
        value=323,
        id='temperature-slider',
    ),
    html.Br(),
    dcc.Slider(
        0.0,
        1,
        step=None,
        marks={
            0.1: '10 % Nafion \nWater Content',
            0.3: '30 % Nafion \nWater Content',
            0.5: '50 % Nafion \nWater Content',
            0.7: '70 % Nafion \nWater Content'
        },
        value=.1,
        id='wetting-slider'
    ),
    html.Br(),
    dcc.Slider(
        0.000005,
        0.0003,

        step=None,
        marks={
            0.00001: '10 µm membrane \nthickness',
            0.000100: '100 µm membrane \thickness',
            0.000150: '150 µm membrane \nthickness',
            0.00025: '250 µm membrane \nthickness'
        },
        value=.0001,
        id='membrane-thickness-slider'
    ),
    html.Br(),
    html.Br(),
    dcc.Graph(id='graph-with-slider'),
    html.Br(),
])


@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('temperature-slider', 'value'),
    Input('wetting-slider', 'value'),
    Input('membrane-thickness-slider', 'value'),
)
def update_figure(selected_temperature, selected_wetting, selected_thickness):
    # Über 0-3 Ampere/cm^2 eine Berechnung mit 0.1 Schritten
    jarray = np.arange(0, 3, 0.02)
    Vohmicarray = ohmicpolarisation(jarray, selected_temperature, selected_wetting, selected_thickness)
    Vcellcarray = np.repeat(ecellvoltage(selected_temperature), jarray.size)
    activationpolarisationarray = activationpolarisation(jarray, selected_temperature)
    # do it like this: https://plotly.com/python/filled-area-plots/

    fig = px.area(x=jarray, y=[Vohmicarray, activationpolarisationarray, Vcellcarray, ])
    newnames = {"wide_variable_0": "V_ohmic",
                "wide_variable_1": "V_act",
                "wide_variable_2": "V_cell",
                }

    fig.for_each_trace(lambda t: t.update(name=newnames[t.name]))
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ))
    fig.update_layout(
        title="Polarisation Curve of Electrolyzer",
        xaxis_title='Current Density (A/cm^2)',
        yaxis_title="Cell Voltage (V)",
        legend_title="Polarisation Resistances",
    )

    fig.update_layout(transition_duration=500)

    return fig


def ecellvoltage(T):
    # not implemented yet
    # pH2, pO2, pH2O,
    """
    Recently only Temperature is considered, partial pressures are neglected
    pH2, pO2, pH2O is the partial pressure of reactants/products,
    T is the temperature in Kelvin, F is the Faraday constant and
    E0rev is the reversible cell potential at standard temperature and pressure. Tamb is ~ 298 K
    """
    # From https://doi.org/10.1016/j.enconman.2022.115917 EQ 14
    E0rev = 1.229 - 0.9 * 0.001 * (T - Tamb)
    E = E0rev

    # Was sind die partiellen Drücke für die Fuel-Cell
    # ignored for now
    # + R * T / (2 * F) * np.log((pH2 * pO2 ** 0.5) / (pH2O))
    return E


def activationpolarisation(i, T):
    # https://doi.org/10.1016/j.jclepro.2020.121184
    # Equation (16)
    Vact = R * T / (ALPPHAA * F) * np.arcsinh(i / (2 * I0A)) + R * T / (ALPHAC * F) * np.arcsinh(i / (2 * I0C))
    return Vact


def ohmicpolarisation(i, T, lamdamembrane, membranethickness):
    membraneconductivity = (0.00514 * lamdamembrane) * np.exp(1268 * (1 / 298 - 1 / T))
    Rohmic = membranethickness / membraneconductivity
    return Rohmic * i


if __name__ == '__main__':
    app.run_server(debug=True)
