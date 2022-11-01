from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import numpy as np

# Definition von Konstanten als globale Variablen
global F
F = 96485.33289 # s A / mol
global R
R = 8.3144598 # J⋅K−1⋅mol−1
# Raumtemperatur 25 °C
global Tamb
Tamb = 298.15 #K

'''
Exchange Current Density and alpha values for Cathode and Anode from:
Yigit, T., Selamet, O.F., 2016. Mathematical modeling and dynamic Simulink simu-
lation of high-pressure PEM electrolyzer system. Int. J. Hydrogen Energy 41,
13901e13914. https://doi.org/10.1016/j.ijhydene.2016.06.022.
'''
global I0A
I0A = 2e-07 #A
global ALPPHAA
ALPPHAA = 2
global I0C
I0C = 2e-03 #A
global ALPHAC
ALPHAC = 0.5

app = Dash(__name__)

server = app.server

app.layout = html.Div([
    html.H1(children='PEM-Electrolyzer Polarisation Curve Simulation',
            style={'width': '75%', 'margin': 15, 'textAlign': 'left', 'font-family': 'Arial'}),

    html.Div(children='''
        Ein interaktives Modell zur 
        Berechnung der Polarisationskurve eines PEM-Elektrolyseurs.
        Ändern Sie mithilfe der Slider die Temperatur, den Wasser-Gehalt des Nafion 
        oder die Nafion-Membran-Dicke und schauen Sie, 
        wie sich das auf die anteiligen Überspannungen auswirkt. 
        Die App wurde in Python geschrieben und nutzt die Module Dash und Numpy. Das Deployment erfolgte über 
        Heroku und gunicorn als WSGI. Quellen und Link zum Source-Code finden Sie ganz unten. 
        Jonas Andrich (2022)
         
        ''',
             style={'width': '75%', 'margin': 10, 'textAlign': 'left', 'font-family': 'Arial'}),
    html.Br(),
    dcc.Slider(
        273,
        398,
        step=None,
        marks={
            298.15: '298.15K / 25°C',
            323.15: '323.15K / 50°C',
            353.15: '353.15K / 80°C',
            373.15: '373.15K / 100°C'
        },
        value=323.15,
        id='temperature-slider',
    ),
    html.Br(),
    dcc.Slider(
        0.0,
        1,
        step=None,
        marks={
            0.1: '10 % Nafion Water Content',
            0.3: '30 % Nafion Water Content',
            0.5: '50 % Nafion Water Content',
            0.7: '70 % Nafion Water Content'
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
            0.00001: '10 µm Membrane Thickness',
            0.000100: '100 µm Membrane Thickness',
            0.000150: '150 µm Membrane Thickness',
            0.00025: '250 µm Membrane Thickness'
        },
        value=.0001,
        id='membrane-thickness-slider'
    ),
    html.Br(),
    html.Br(),
    dcc.Graph(id='graph-with-slider'),
    html.Br(),
    dcc.Markdown('''
            #### Quellen:
            Falcão, D. S., & Pinto, A. M. F. R. (2020). A review on PEM Electrolyzer Modelling: guidelines for beginners. 
            Journalof Cleaner Production, 121184. 
            https://doi.org/10.1016/j.jclepro.2020.121184
            
            Folgado, F. J., González, I., & Calderón, A. J. (2022). Simulation platform for the assessment of 
            PEM electrolyzer models oriented to implement digital Replicas. Energy Conversion and Management, 267, 115917.
            https://doi.org/10.1016/j.enconman.2022.115917
        
            Yigit, T., Selamet, O.F. (2016). Mathematical modeling and dynamic Simulink simulation of high-pressure PEM 
            electrolyzer system. Int. J. Hydrogen Energy 41,13901e13914. 
            https://doi.org/10.1016/j.ijhydene.2016.06.022.
            
            
            #### Source Code:
            https://github.com/JonasAndrich/ElektrolyzerModel/blob/master/main.py
            
            ''', style={'width': '100%', 'margin': 0, 'textAlign': 'left', 'font-family': 'Arial'}
                 ),
    dcc.Markdown('''
            #### Beispiel-Abbildung eines PEM-Elektrolyseurs von Wikipedia:

            ''', style={'width': '100%', 'margin': 0, 'textAlign': 'left', 'font-family': 'Arial'}
                 ),

    html.A(
        href ="https://en.wikipedia.org/wiki/Polymer_electrolyte_membrane_electrolysis",
        children=[
            html.Img(
                alt="Scheme of PEM Water Electrolysis Cell from Wikipedia",
                src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/PEMelectrolysis.jpg/220px-PEMelectrolysis.jpg",
            )
        ]
    )
])


@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('temperature-slider', 'value'),
    Input('wetting-slider', 'value'),
    Input('membrane-thickness-slider', 'value'),
)
def update_figure(selected_temperature, selected_wetting, selected_thickness):
    # Über 0-3 Ampere/cm^2 eine Berechnung mit 0.1 Schritten
    jarray = np.arange(0, 3, 0.01)

    #Berechnung der verschiedenen Polarisations-Anteile
    Vohmicarray = ohmicpolarisation(jarray, selected_temperature, selected_wetting, selected_thickness)
    Vcellcarray = np.repeat(ecellvoltage(selected_temperature), jarray.size)
    anodeactivationpolarisationarray = anodeactivationpolarisation(jarray, selected_temperature)
    cathodeactivationpolarisationarray = cathodeactivationpolarisation(jarray, selected_temperature)

    # Power Curve to implement
    # power = Ecell * i


    # Plotten erfolgt wie in folgendem Beispiel: https://plotly.com/python/filled-area-plots/
    fig = px.area(x=jarray, y=[Vohmicarray, anodeactivationpolarisationarray, cathodeactivationpolarisationarray, Vcellcarray, ])
    newnames = {"wide_variable_0": "V_ohmic",
                "wide_variable_1": "V_anode_act",
                "wide_variable_2": "V_cathode_act",
                "wide_variable_3": "V_cell",
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

    """
    Recently only Temperature is considered, partial pressures are neglected
    pH2, pO2, pH2O is the partial pressure of reactants/products,
    T is the temperature in Kelvin, F is the Faraday constant and
    E0rev is the reversible cell potential at standard temperature and pressure. Tamb is ~ 298 K
    """

    # From https://doi.org/10.1016/j.enconman.2022.115917
    # Equation 14
    E0rev = 1.229 - 0.9 * 0.001 * (T - Tamb)
    E = E0rev

    # Partielle Drücke aus Gleichung 14 für die Fuel-Cell bisher ignoriert
    # + R * T / (2 * F) * np.log((pH2 * pO2 ** 0.5) / (pH2O))
    return E


def anodeactivationpolarisation(i, T):
    # https://doi.org/10.1016/j.jclepro.2020.121184
    # Equation (16) Anode part

    Vaact = R * T / (ALPPHAA * F) * np.arcsinh(i / (2 * I0A))
    return Vaact
def cathodeactivationpolarisation(i, T):
    # https://doi.org/10.1016/j.jclepro.2020.121184
    # Equation (16) Cathode part
    Vcact = R * T / (ALPHAC * F) * np.arcsinh(i / (2 * I0C))
    return Vcact

def activationpolarisation(i, T):
    # https://doi.org/10.1016/j.jclepro.2020.121184
    # Equation (16)
    Vact = R * T / (ALPPHAA * F) * np.arcsinh(i / (2 * I0A)) + R * T / (ALPHAC * F) * np.arcsinh(i / (2 * I0C))
    return Vact


def ohmicpolarisation(i, T, lamdamembrane, membranethickness):
    # https://doi.org/10.1016/j.jclepro.2020.121184
    # Equation (23)
    membraneconductivity = (0.00514 * lamdamembrane) * np.exp(1268 * (1 / 303 - 1 / T))
    Rohmic = membranethickness / membraneconductivity
    return Rohmic * i


if __name__ == '__main__':
    app.run_server(debug=True)
