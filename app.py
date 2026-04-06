# ╔══════════════════════════════════════════════════════════════╗
# ║         JAPAN CLIMATE DASHBOARD — JUPYTER NOTEBOOK          ║
# ╚══════════════════════════════════════════════════════════════╝

# ═══════════════════════════════════════════════════════════════
# CELL 1 — Install (run once)
# ═══════════════════════════════════════════════════════════════
# !pip install dash dash-bootstrap-components plotly pandas openpyxl

# ═══════════════════════════════════════════════════════════════
# CELL 2 — Imports
# ═══════════════════════════════════════════════════════════════
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# ═══════════════════════════════════════════════════════════════
# CELL 3 — Load & Prepare Data  
# ═══════════════════════════════════════════════════════════════
import pandas as pd

f1 = pd.read_excel("Main data file 1.xlsx")
f2 = pd.read_excel("Main Data File 2.xlsx")

# Rename File 1 columns to match what the code expects
f1.columns = [
    'country', 'year', 'co2_total', 'co2_share', 'co2_per_capita',
    'co2_consumption', 'population', 'other_renewables', 'biofuels', 'solar', 'wind',
    'hydropower', 'nuclear', 'gas', 'coal', 'oil'
]

# GDP bubble lookup — 2023 only (from File 2 columns Entity/Year/GDP per capita)
_gdp_bubble = (
    f2[['Entity', 'Year', 'GDP per capita']]
    .dropna()
    .rename(columns={'Entity': 'country', 'Year': 'year', 'GDP per capita': 'gdp_per_capita'})
    .query('year == 2023')
    .set_index('country')['gdp_per_capita']
    .to_dict()
)
_gdp_bubble['World'] = 21000

# GDP time series (from File 2 columns country/year/GDP per capita.1)
_gdp_ts = (
    f2[['country', 'year', 'GDP per capita.1']]
    .dropna(subset=['GDP per capita.1'])
    .rename(columns={'GDP per capita.1': 'gdp_per_capita'})
    .copy()
)
_gdp_ts['year'] = _gdp_ts['year'].astype(int)

# Merge into main df
df = f1[f1['year'] >= 1990].copy()
df = df.merge(_gdp_ts, on=['country', 'year'], how='left')

japan = df[df['country'] == 'Japan'].reset_index(drop=True)
india = df[df['country'] == 'India'].reset_index(drop=True)
world = df[df['country'] == 'World'].reset_index(drop=True)

japan['co2_mt']     = japan['co2_total'] / 1e9
japan['renewables'] = japan['solar'] + japan['wind'] + japan['hydropower'] + japan['other_renewables']

co2_2023      = japan[japan['year'] == 2023]['co2_mt'].values[0]
pc_2023       = japan[japan['year'] == 2023]['co2_per_capita'].values[0]
pc_1990       = japan[japan['year'] == 1990]['co2_per_capita'].values[0]
pct_change    = round(((pc_2023 - pc_1990) / pc_1990) * 100, 1)
share_2023    = japan[japan['year'] == 2023]['co2_share'].values[0]
world_pc_2023 = world[world['year'] == 2023]['co2_per_capita'].values[0]
india_pc_2023 = india[india['year'] == 2023]['co2_per_capita'].values[0]

print("✅ Data loaded")
print(f"   CO₂ 2023: {co2_2023:.1f} MtCO₂ | Per capita: {pc_2023:.2f} t | Change since 1990: {pct_change}%")
 

# ═══════════════════════════════════════════════════════════════
# CELL 4 — Design Tokens (Light Wabi-Sabi theme)
# ═══════════════════════════════════════════════════════════════
BG        = '#F7F7F5'
CARD_BG   = '#FFFFFF'
RED       = '#D9381E'
BLUE      = '#1F456E'
GREEN     = '#4A6B53'
YELLOW    = '#B8860B'
TEXT      = '#1A1A1A'
SUBTEXT   = '#737373'
BORDER    = '#E0E0DC'
FONT_HEAD = 'Shippori Mincho, Georgia, serif'
FONT_BODY = 'Inter, Helvetica Neue, sans-serif'

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=FONT_BODY, color=TEXT, size=12),
    margin=dict(l=40, r=20, t=90, b=40),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=SUBTEXT, size=11),
                orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    xaxis=dict(showgrid=False, color=SUBTEXT, tickfont=dict(color=SUBTEXT),
               linecolor=BORDER, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor=BORDER, color=SUBTEXT,
               tickfont=dict(color=SUBTEXT), linecolor='rgba(0,0,0,0)', zeroline=False),
    hoverlabel=dict(bgcolor=CARD_BG, bordercolor=BORDER,
                    font=dict(family=FONT_BODY, color=TEXT))
)

ENERGY_COLORS = {
    'coal':       ('#8B7355', 'rgba(139,115,85,0.75)'),
    'oil':        ('#B8860B', 'rgba(184,134,11,0.75)'),
    'gas':        ('#CD853F', 'rgba(205,133,63,0.75)'),
    'nuclear':    ('#1F456E', 'rgba(31,69,110,0.75)'),
    'renewables': ('#4A6B53', 'rgba(74,107,83,0.75)'),
}
ENERGY_LABELS = {'coal':'Coal','oil':'Oil','gas':'Gas','nuclear':'Nuclear','renewables':'Renewables'}

print("✅ Design tokens set")

# ═══════════════════════════════════════════════════════════════
# CELL 5 — Static Charts (built once, callbacks will update some)
# ═══════════════════════════════════════════════════════════════

# Total CO2
fig_total = go.Figure()
fig_total.add_trace(go.Scatter(
    x=japan['year'], y=japan['co2_mt'], mode='lines',
    line=dict(color=RED, width=3), fill='tozeroy', fillcolor='rgba(217,56,30,0.08)',
    hovertemplate='<b>%{x}</b><br>%{y:.1f} MtCO₂<extra></extra>'
))
for yr, lbl in [(2011,'Fukushima'),(2016,'Paris Agmt')]:
    fig_total.add_vline(x=yr, line_dash='dash', line_color=SUBTEXT, line_width=1, opacity=0.5)
    fig_total.add_annotation(x=yr, y=japan['co2_mt'].max(), text=lbl, showarrow=False,
        font=dict(color=SUBTEXT, size=10, family=FONT_BODY), xshift=5, yshift=10)
fig_total.update_layout(**PLOTLY_LAYOUT,
    title=dict(text='Total CO₂ Emissions (MtCO₂)', font=dict(color=TEXT, size=14, family=FONT_HEAD)),
    yaxis_title='MtCO₂')

# Per Capita
fig_pc = go.Figure()
fig_pc.add_trace(go.Scatter(
    x=japan['year'], y=japan['co2_per_capita'], mode='lines',
    line=dict(color=BLUE, width=3), fill='tozeroy', fillcolor='rgba(31,69,110,0.08)',
    hovertemplate='<b>%{x}</b><br>%{y:.2f} tCO₂/person<extra></extra>'
))
for yr, lbl in [(2011,'Fukushima'),(2016,'Paris Agmt')]:
    fig_pc.add_vline(x=yr, line_dash='dash', line_color=SUBTEXT, line_width=1, opacity=0.5)
    fig_pc.add_annotation(x=yr, y=japan['co2_per_capita'].max(), text=lbl, showarrow=False,
        font=dict(color=SUBTEXT, size=10, family=FONT_BODY), xshift=5, yshift=10)
fig_pc.update_layout(**PLOTLY_LAYOUT,
    title=dict(text='Per Capita CO₂ Emissions (tCO₂/person)', font=dict(color=TEXT, size=14, family=FONT_HEAD)),
    yaxis_title='tCO₂/person')

# Comparison
fig_compare = go.Figure()
for entity, data, color, dash in [('Japan',japan,RED,'solid'),('India',india,GREEN,'dot'),('World',world,BLUE,'dash')]:
    fig_compare.add_trace(go.Scatter(
        x=data['year'], y=data['co2_per_capita'], mode='lines', name=entity,
        line=dict(color=color, width=2.5, dash=dash),
        hovertemplate=f'<b>{entity} %{{x}}</b><br>%{{y:.2f}} tCO₂/person<extra></extra>'
    ))
fig_compare.update_layout(**PLOTLY_LAYOUT,
    title=dict(text='Per Capita CO₂: Japan vs India vs World', font=dict(color=TEXT, size=14, family=FONT_HEAD)),
    yaxis_title='tCO₂/person')

# Donut
japan_share = round(share_2023, 2)
fig_donut = go.Figure(go.Pie(
    labels=['Japan','Rest of World'], values=[japan_share, round(100-japan_share,2)],
    hole=0.65, marker=dict(colors=[RED, BORDER]), textinfo='none',
    hovertemplate='<b>%{label}</b><br>%{value:.2f}%<extra></extra>'
))
fig_donut.add_annotation(text=f'<b>{japan_share}%</b>', x=0.5, y=0.5, showarrow=False,
    font=dict(color=TEXT, size=20, family=FONT_HEAD), align='center')

# Apply base layout first, then apply overrides
fig_donut.update_layout(**PLOTLY_LAYOUT)
fig_donut.update_layout(
    title=dict(text="Japan's Share of Global CO₂ (2023)", font=dict(color=TEXT, size=14, family=FONT_HEAD)),
    showlegend=True,
    legend=dict(orientation='h', yanchor='top', y=-0.1, xanchor='center', x=0.5)
)

# Scatter
fig_scatter = go.Figure()
fig_scatter.add_trace(go.Scatter(
    x=japan['gdp_per_capita'], y=japan['co2_per_capita'],
    mode='markers+text', text=japan['year'].astype(str),
    textposition='top center', textfont=dict(color=SUBTEXT, size=9),
    marker=dict(size=10, color=japan['year'],
        colorscale=[[0,'#E8D5C4'],[0.5,RED],[1,'#8B1A0A']], showscale=True,
        colorbar=dict(title=dict(text='Year', font=dict(color=SUBTEXT)),
                      tickfont=dict(color=SUBTEXT), outlinewidth=0)),
    hovertemplate='<b>%{text}</b><br>GDP: $%{x:,.0f}<br>CO₂: %{y:.2f} t/person<extra></extra>'
))
fig_scatter.update_layout(**PLOTLY_LAYOUT,
    title=dict(text='GDP per Capita vs Per Capita CO₂ (1990–2024)',
               font=dict(color=TEXT, size=14, family=FONT_HEAD)),
    xaxis_title='GDP per Capita (USD)', yaxis_title='CO₂ per Capita (tCO₂/person)')

# Justice bar
_bar = go.Figure(data=[go.Bar(
    x=['Japan','World Average','India'], y=[pc_2023, world_pc_2023, india_pc_2023],
    marker=dict(color=[RED,BLUE,GREEN], opacity=0.85),
    text=[f'{v:.2f}t' for v in [pc_2023, world_pc_2023, india_pc_2023]],
    textposition='outside', textfont=dict(color=TEXT, size=13, family=FONT_HEAD),
    hovertemplate='<b>%{x}</b><br>%{y:.2f} tCO₂/person<extra></extra>'
)])
_bar.update_layout(**PLOTLY_LAYOUT,
    title=dict(text='Per Capita CO₂ Comparison (2023)', font=dict(color=TEXT, size=14, family=FONT_HEAD)),
    yaxis_title='tCO₂/person', showlegend=False, height=320)
_bar.update_yaxes(range=[0, max(pc_2023, world_pc_2023, india_pc_2023)*1.3])

# Justice bubble
_bubble = go.Figure(data=[
    go.Scatter(
        x=[_gdp_bubble.get('Japan')],
        y=[pc_2023],
        mode='markers+text', name='Japan', text=['Japan'],
        textposition='top center',
        textfont=dict(color=TEXT, size=13, family=FONT_HEAD),
        marker=dict(
            size=max(30, int(japan[japan['year'] == 2023]['population'].values[0] / 8_000_000)),
            color=RED, opacity=0.75, line=dict(color='white', width=2)
        ),
        hovertemplate='<b>Japan</b><br>GDP: $%{x:,.0f}<br>CO₂: %{y:.2f} t/person<extra></extra>'
    ),
    go.Scatter(
        x=[_gdp_bubble.get('India')],
        y=[india_pc_2023],
        mode='markers+text', name='India', text=['India'],
        textposition='top center',
        textfont=dict(color=TEXT, size=13, family=FONT_HEAD),
        marker=dict(
            size=max(30, int(india[india['year'] == 2023]['population'].values[0] / 8_000_000)),
            color=GREEN, opacity=0.75, line=dict(color='white', width=2)
        ),
        hovertemplate='<b>India</b><br>GDP: $%{x:,.0f}<br>CO₂: %{y:.2f} t/person<extra></extra>'
    ),
    go.Scatter(
        x=[_gdp_bubble.get('World')],
        y=[world_pc_2023],
        mode='markers+text', name='World Avg', text=['World Avg'],
        textposition='top center',
        textfont=dict(color=TEXT, size=13, family=FONT_HEAD),
        marker=dict(size=40, color=BLUE, opacity=0.75, line=dict(color='white', width=2)),
        hovertemplate='<b>World Avg</b><br>GDP: $%{x:,.0f}<br>CO₂: %{y:.2f} t/person<extra></extra>'
    ),
])
_bubble.update_layout(**PLOTLY_LAYOUT,
    title=dict(text='Wealth vs Emissions — Bubble size reflects population (2023)',
               font=dict(color=TEXT, size=14, family=FONT_HEAD)),
    xaxis_title='GDP per Capita (USD)', yaxis_title='Per Capita CO₂ (tCO₂/person)',
    height=360, showlegend=True)

print("✅ All charts built")

# ═══════════════════════════════════════════════════════════════
# CELL 6 — Helper UI Components
# ═══════════════════════════════════════════════════════════════

def kpi_card(title, value, unit, color=RED, trend=None):
    return html.Div([
        html.P(title, style={'color':SUBTEXT,'fontSize':'11px','letterSpacing':'1.5px',
            'textTransform':'uppercase','margin':'0 0 8px 0','fontFamily':FONT_BODY}),
        html.Div([
            html.Span(value, style={'color':color,'fontSize':'32px','fontWeight':'700',
                'fontFamily':FONT_HEAD,'lineHeight':'1'}),
            html.Span(f' {unit}', style={'color':SUBTEXT,'fontSize':'13px',
                'marginLeft':'4px','fontFamily':FONT_BODY}),
        ]),
        html.P(trend or '', style={'color':SUBTEXT,'fontSize':'11px',
            'margin':'6px 0 0 0','fontFamily':FONT_BODY}),
    ], style={'background':CARD_BG,'border':f'1px solid {BORDER}',
        'borderTop':f'2px solid {color}','borderRadius':'8px',
        'padding':'20px','flex':'1','minWidth':'180px'})

def section_label(text):
    return html.P(text, style={'color':SUBTEXT,'fontSize':'10px','letterSpacing':'3px',
        'textTransform':'uppercase','fontFamily':FONT_BODY,'marginBottom':'12px',
        'borderLeft':f'2px solid {RED}','paddingLeft':'10px'})

def section_title(text):
    return html.H2(text, style={'color':TEXT,'fontFamily':FONT_HEAD,'fontSize':'28px',
        'fontWeight':'400','margin':'0 0 32px 0','letterSpacing':'-0.5px'})

def chart_card(fig, gid=None):
    kwargs = {'figure': fig, 'config': {'displayModeBar': False}}
    if gid:
        kwargs['id'] = gid
    return html.Div(dcc.Graph(**kwargs),
        style={'background':CARD_BG,'borderRadius':'8px','padding':'8px','border':f'1px solid {BORDER}'})

print("✅ UI helpers defined")

# ═══════════════════════════════════════════════════════════════
# CELL 7 — App & Layout
# ═══════════════════════════════════════════════════════════════

app = Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    'https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@400;700&family=Inter:wght@300;400;500;600&display=swap'
])
server = app.server
app.index_string = '''
<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>Japan Climate Dashboard</title>
{%favicon%}
{%css%}
<style>
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { background: #F7F7F5; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #F7F7F5; }
    ::-webkit-scrollbar-thumb { background: #E0E0DC; border-radius: 3px; }
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
'''

# ── LANDING ──────────────────────────────────────────────────
landing = html.Div(id='landing', style={
    'height':'100vh',
    'backgroundImage':'url(https://images.unsplash.com/photo-1490806843957-31f4c9a91c65?w=1600&q=80)',
    'backgroundSize':'cover','backgroundPosition':'center 40%',
    'position':'relative','display':'flex','alignItems':'center',
    'justifyContent':'center','flexDirection':'column','textAlign':'center'
}, children=[
    html.Div(style={'position':'absolute','inset':'0',
        'background':'linear-gradient(to bottom, rgba(8,12,20,0.55) 0%, rgba(8,12,20,0.75) 60%, rgba(8,12,20,1) 100%)',
        'zIndex':'0'}),
    html.Div(style={'position':'relative','zIndex':'1','padding':'0 20px'}, children=[
        html.P('TISS Mumbai · BS Analytics & Sustainability Studies', style={
            'color':'#86868B','fontSize':'11px','letterSpacing':'3px',
            'textTransform':'uppercase','fontFamily':FONT_BODY,'marginBottom':'24px'}),
        html.H1("JAPAN'S CLIMATE SHIFT", style={
            'color':'#F5F5F7','fontFamily':FONT_HEAD,
            'fontSize':'clamp(36px, 7vw, 80px)','fontWeight':'700',
            'letterSpacing':'-2px','margin':'0 0 16px 0','lineHeight':'1'}),
        html.P('A 35-Year Data Story: 1990 – 2024', style={
            'color':'#86868B','fontFamily':FONT_BODY,
            'fontSize':'clamp(14px, 2vw, 18px)','fontWeight':'300',
            'letterSpacing':'2px','marginBottom':'48px'}),
        html.A('Explore the Data →', href='#dashboard', style={
            'display':'inline-block','background':'rgba(217,56,30,0.12)',
            'color':RED,'border':f'1px solid {RED}','padding':'14px 40px',
            'borderRadius':'2px','fontSize':'13px','letterSpacing':'2px',
            'textTransform':'uppercase','textDecoration':'none',
            'fontFamily':FONT_BODY,'fontWeight':'500'}),
    ]),
    html.Div('↓', style={'position':'absolute','bottom':'30px',
        'color':'#86868B','fontSize':'20px','zIndex':'1'})
])

# ── MAIN DASHBOARD ────────────────────────────────────────────
dashboard = html.Div(id='dashboard', style={
    'padding':'80px 5% 60px','maxWidth':'1400px','margin':'0 auto'
}, children=[

    section_label('Climate Data Analysis · Japan 1990–2024'),
    section_title('Carbon Footprint at a Glance'),

    # KPI Row
    html.Div(style={'display':'flex','gap':'16px','flexWrap':'wrap','marginBottom':'60px'}, children=[
        kpi_card('Total CO₂ Emissions',  f'{co2_2023:.1f}',   'MtCO₂',  RED,    '2023 figure'),
        kpi_card('Per Capita Emissions', f'{pc_2023:.2f}',    't/person',BLUE,   '2023 figure'),
        kpi_card('Change Since 1990',    f'{pct_change}%',    '',        GREEN if pct_change < 0 else RED, 'Per capita change'),
        kpi_card('Global CO₂ Share',     f'{share_2023:.2f}', '%',       YELLOW, '2023 share'),
    ]),

    # Year Slider
    html.Div(style={'background':CARD_BG,'border':f'1px solid {BORDER}',
        'borderRadius':'8px','padding':'24px 32px','marginBottom':'40px'}, children=[
        html.P('FILTER BY YEAR RANGE', style={'color':SUBTEXT,'fontSize':'9px',
            'letterSpacing':'3px','fontFamily':FONT_BODY,'marginBottom':'18px'}),
        dcc.RangeSlider(
            id='year-slider', min=1990, max=2024, step=1, value=[1990, 2024],
            marks={y: {'label':str(y),'style':{'color':SUBTEXT,'fontSize':'11px'}}
                   for y in range(1990, 2025, 2)},
            tooltip={'placement':'bottom','always_visible':False}
        )
    ]),

    # Emissions Trends
    html.Div(style={'marginBottom':'60px'}, children=[
        section_label('Task B · Emissions Trend Analysis'),
        section_title('Two Decades of Carbon'),
        html.Div(style={'display':'grid','gridTemplateColumns':'1fr 1fr','gap':'24px'}, children=[
            chart_card(fig_total, gid='chart-total'),
            chart_card(fig_pc,    gid='chart-pc'),
        ])
    ]),

    # Energy Mix with dropdown
    html.Div(style={'marginBottom':'60px'}, children=[
        section_label('Task B Extended · Energy Transition'),
        section_title('The Energy Story'),
        html.Div(style={'background':CARD_BG,'border':f'1px solid {BORDER}',
            'borderRadius':'8px','padding':'20px 24px','marginBottom':'16px'}, children=[
            html.Div(style={'display':'flex','alignItems':'center','gap':'16px',
                'marginBottom':'16px','flexWrap':'wrap'}, children=[
                html.P('SELECT SOURCES:', style={'color':SUBTEXT,'fontSize':'9px',
                    'letterSpacing':'2px','fontFamily':FONT_BODY,'margin':'0','whiteSpace':'nowrap'}),
                dcc.Dropdown(
                    id='energy-dropdown',
                    options=[
                        {'label':'Coal',       'value':'coal'},
                        {'label':'Oil',        'value':'oil'},
                        {'label':'Gas',        'value':'gas'},
                        {'label':'Nuclear',    'value':'nuclear'},
                        {'label':'Renewables', 'value':'renewables'},
                    ],
                    value=['coal','oil','gas','nuclear','renewables'],
                    multi=True,
                    style={'flex':'1','minWidth':'300px','fontFamily':FONT_BODY,'fontSize':'12px'}
                ),
            ]),
            dcc.Graph(id='chart-energy', config={'displayModeBar':False})
        ]),
        html.P(
            "Nuclear energy collapsed after the 2011 Fukushima disaster, forcing Japan to surge fossil fuel use. "
            "Renewables have gradually grown post-2015 under Japan's Feed-in Tariff policy.",
            style={'color':SUBTEXT,'fontSize':'13px','marginTop':'16px',
                   'fontFamily':FONT_BODY,'lineHeight':'1.7','maxWidth':'800px'}
        )
    ]),

    # Comparison + Donut
    html.Div(style={'marginBottom':'60px'}, children=[
        section_label('Task C · Carbon Inequality Analysis'),
        section_title('Japan in the World'),
        # Country dropdown
        html.Div(style={'background':CARD_BG,'border':f'1px solid {BORDER}',
            'borderRadius':'8px','padding':'20px 24px','marginBottom':'16px'}, children=[
            html.Div(style={'display':'flex','alignItems':'center','gap':'16px','flexWrap':'wrap'}, children=[
                html.P('ADD COUNTRIES TO COMPARE:', style={'color':SUBTEXT,'fontSize':'9px',
                    'letterSpacing':'2px','fontFamily':FONT_BODY,'margin':'0','whiteSpace':'nowrap'}),
                dcc.Dropdown(
                    id='country-dropdown',
                    options=[{'label': c, 'value': c} for c in sorted(
    df[~df['country'].isin(['Japan', 'India', 'World'])]['country'].unique()
)],
                    value=[],
                    multi=True,
                    placeholder='Select countries to add...',
                    style={'flex':'1','minWidth':'300px','fontFamily':FONT_BODY,'fontSize':'12px'}
                ),
            ])
        ]),
        html.Div(style={'display':'grid','gridTemplateColumns':'2fr 1fr','gap':'24px'}, children=[
            chart_card(fig_compare, gid='chart-compare'),
            chart_card(fig_donut, gid='chart-donut'),
        ])
    ]),

    # Scatter
    html.Div(style={'marginBottom':'60px'}, children=[
        section_label('Task D · Wealth vs Emissions'),
        section_title('GDP Growth & Carbon Decoupling'),
        chart_card(fig_scatter),
        html.P(
            "Each point is one year. Rising GDP alongside falling emissions shows Japan's "
            "economic growth is increasingly decoupled from carbon output.",
            style={'color':SUBTEXT,'fontSize':'13px','marginTop':'16px',
                   'fontFamily':FONT_BODY,'lineHeight':'1.7','maxWidth':'800px'}
        )
    ]),
])

# ── CLIMATE JUSTICE ───────────────────────────────────────────
justice = html.Div(id='climate-justice', style={
    'background':'#EFEFEC','borderTop':f'2px solid {BORDER}','padding':'80px 5%',
}, children=[
    html.Div(style={'maxWidth':'1100px','margin':'0 auto'}, children=[

        section_label('Task E · Climate Justice Analysis'),
        section_title('Who Bears the Responsibility?'),

        # Stat panels
        html.Div(style={'display':'grid','gridTemplateColumns':'1fr 1fr 1fr','gap':'2px',
            'marginBottom':'40px','border':f'1px solid {BORDER}','borderRadius':'6px','overflow':'hidden'}, children=[
            html.Div([
                html.P('JAPAN', style={'color':SUBTEXT,'fontSize':'9px','letterSpacing':'3px','fontFamily':FONT_BODY,'margin':'0 0 10px 0'}),
                html.P(f'{pc_2023:.1f}t', style={'color':RED,'fontSize':'48px','fontFamily':FONT_HEAD,'fontWeight':'700','margin':'0','lineHeight':'1'}),
                html.P('per capita CO₂ (2023)', style={'color':SUBTEXT,'fontSize':'12px','fontFamily':FONT_BODY,'margin':'8px 0 4px 0'}),
                html.P(f'{round(pc_2023/world_pc_2023,1)}× the world average', style={'color':RED,'fontSize':'12px','fontWeight':'600','fontFamily':FONT_BODY,'margin':'0'}),
            ], style={'background':CARD_BG,'padding':'32px','borderLeft':f'4px solid {RED}'}),

            html.Div([
                html.P('WORLD AVERAGE', style={'color':SUBTEXT,'fontSize':'9px','letterSpacing':'3px','fontFamily':FONT_BODY,'margin':'0 0 10px 0'}),
                html.P(f'{world_pc_2023:.1f}t', style={'color':BLUE,'fontSize':'48px','fontFamily':FONT_HEAD,'fontWeight':'700','margin':'0','lineHeight':'1'}),
                html.P('per capita CO₂ (2023)', style={'color':SUBTEXT,'fontSize':'12px','fontFamily':FONT_BODY,'margin':'8px 0 4px 0'}),
                html.P('Global benchmark', style={'color':BLUE,'fontSize':'12px','fontWeight':'600','fontFamily':FONT_BODY,'margin':'0'}),
            ], style={'background':CARD_BG,'padding':'32px','borderLeft':f'4px solid {BLUE}'}),

            html.Div([
                html.P('INDIA', style={'color':SUBTEXT,'fontSize':'9px','letterSpacing':'3px','fontFamily':FONT_BODY,'margin':'0 0 10px 0'}),
                html.P(f'{india_pc_2023:.1f}t', style={'color':GREEN,'fontSize':'48px','fontFamily':FONT_HEAD,'fontWeight':'700','margin':'0','lineHeight':'1'}),
                html.P('per capita CO₂ (2023)', style={'color':SUBTEXT,'fontSize':'12px','fontFamily':FONT_BODY,'margin':'8px 0 4px 0'}),
                html.P(f'Japan emits {round(pc_2023/india_pc_2023,1)}× more per person', style={'color':GREEN,'fontSize':'12px','fontWeight':'600','fontFamily':FONT_BODY,'margin':'0'}),
            ], style={'background':CARD_BG,'padding':'32px','borderLeft':f'4px solid {GREEN}'}),
        ]),

        # Bar chart
        html.Div(style={'background':CARD_BG,'border':f'1px solid {BORDER}',
            'borderRadius':'6px','padding':'8px','marginBottom':'24px'}, children=[
            dcc.Graph(figure=_bar, config={'displayModeBar':False})
        ]),

        # Bubble chart
        html.Div(style={'background':CARD_BG,'border':f'1px solid {BORDER}',
            'borderRadius':'8px','padding':'20px 24px','marginBottom':'8px'}, children=[
            html.Div(style={'display':'flex','alignItems':'center','gap':'16px','flexWrap':'wrap'}, children=[
                html.P('ADD COUNTRIES TO BUBBLE:', style={'color':SUBTEXT,'fontSize':'9px',
                    'letterSpacing':'2px','fontFamily':FONT_BODY,'margin':'0','whiteSpace':'nowrap'}),
                dcc.Dropdown(
                    id='bubble-dropdown',
                    options=[{'label': c, 'value': c} for c in sorted(
    df[~df['country'].isin(['Japan', 'India', 'World'])]['country'].unique()
) if c in _gdp_bubble],
                    value=[],
                    multi=True,
                    placeholder='Select countries to add...',
                    style={'flex':'1','minWidth':'300px','fontFamily':FONT_BODY,'fontSize':'12px'}
                ),
            ])
        ]),
        html.Div(style={'background':CARD_BG,'border':f'1px solid {BORDER}',
            'borderRadius':'6px','padding':'8px','marginBottom':'40px'}, children=[
            dcc.Graph(id='chart-bubble', figure=_bubble, config={'displayModeBar':False})
        ]),

        # Sources + footer
        html.Div(style={'borderTop':f'1px solid {BORDER}','paddingTop':'28px'}, children=[
            html.P('Data Sources', style={'color':TEXT,'fontFamily':FONT_HEAD,'fontSize':'15px','marginBottom':'10px'}),
            html.P('Our World in Data — CO₂ and Greenhouse Gas Emissions (2024). ourworldindata.org/co2-emissions',
                   style={'color':SUBTEXT,'fontSize':'11px','fontFamily':FONT_BODY,'margin':'3px 0'}),
            html.P('Our World in Data — Energy Mix (2024). ourworldindata.org/energy-mix',
                   style={'color':SUBTEXT,'fontSize':'11px','fontFamily':FONT_BODY,'margin':'3px 0'}),
            html.P('World Bank — GDP per Capita (2024). data.worldbank.org',
                   style={'color':SUBTEXT,'fontSize':'11px','fontFamily':FONT_BODY,'margin':'3px 0'}),
            html.Div(style={'marginTop':'20px','paddingTop':'20px','borderTop':f'1px solid {BORDER}'}, children=[
                html.P('BS in Analytics and Sustainability Studies (2024–28) · TISS Mumbai  ·  Climate Change, Sustainability and Development · Assignment I',
                       style={'color':SUBTEXT,'fontSize':'10px','fontFamily':FONT_BODY,'letterSpacing':'0.5px'}),
            ])
        ])
    ])
])

app.layout = html.Div(
    style={'backgroundColor':BG,'fontFamily':FONT_BODY},
    children=[landing, dashboard, justice]
)

print("✅ Layout built")

# ═══════════════════════════════════════════════════════════════
# CELL 8 — Callbacks
# ═══════════════════════════════════════════════════════════════

@app.callback(
    Output('chart-total', 'figure'),
    Output('chart-pc',    'figure'),
    Input('year-slider',  'value')
)
def update_trends(year_range):
    y0, y1 = year_range
    j = japan[(japan['year'] >= y0) & (japan['year'] <= y1)]

    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(x=j['year'], y=j['co2_mt'], mode='lines',
        line=dict(color=RED, width=3), fill='tozeroy', fillcolor='rgba(217,56,30,0.08)',
        hovertemplate='<b>%{x}</b><br>%{y:.1f} MtCO₂<extra></extra>'))
    for yr, lbl in [(2011,'Fukushima'),(2016,'Paris Agmt')]:
        if y0 <= yr <= y1:
            fig_t.add_vline(x=yr, line_dash='dash', line_color=SUBTEXT, line_width=1, opacity=0.5)
            fig_t.add_annotation(x=yr, y=j['co2_mt'].max(), text=lbl, showarrow=False,
                font=dict(color=SUBTEXT, size=10, family=FONT_BODY), xshift=5, yshift=10)
    fig_t.update_layout(**PLOTLY_LAYOUT,
        title=dict(text='Total CO₂ Emissions (MtCO₂)', font=dict(color=TEXT, size=14, family=FONT_HEAD)),
        yaxis_title='MtCO₂')

    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(x=j['year'], y=j['co2_per_capita'], mode='lines',
        line=dict(color=BLUE, width=3), fill='tozeroy', fillcolor='rgba(31,69,110,0.08)',
        hovertemplate='<b>%{x}</b><br>%{y:.2f} tCO₂/person<extra></extra>'))
    for yr, lbl in [(2011,'Fukushima'),(2016,'Paris Agmt')]:
        if y0 <= yr <= y1:
            fig_p.add_vline(x=yr, line_dash='dash', line_color=SUBTEXT, line_width=1, opacity=0.5)
            fig_p.add_annotation(x=yr, y=j['co2_per_capita'].max(), text=lbl, showarrow=False,
                font=dict(color=SUBTEXT, size=10, family=FONT_BODY), xshift=5, yshift=10)
    fig_p.update_layout(**PLOTLY_LAYOUT,
        title=dict(text='Per Capita CO₂ Emissions (tCO₂/person)', font=dict(color=TEXT, size=14, family=FONT_HEAD)),
        yaxis_title='tCO₂/person')

    return fig_t, fig_p


@app.callback(
    Output('chart-energy', 'figure'),
    Input('energy-dropdown', 'value'),
    Input('year-slider',     'value')
)
def update_energy(selected, year_range):
    y0, y1 = year_range
    j = japan[(japan['year'] >= y0) & (japan['year'] <= y1)]
    fig = go.Figure()
    if selected:
        for src in selected:
            lc, fc = ENERGY_COLORS[src]
            fig.add_trace(go.Scatter(
                x=j['year'], y=j[src], mode='lines', name=ENERGY_LABELS[src],
                stackgroup='one', line=dict(width=0.5, color=lc), fillcolor=fc,
                hovertemplate=f'<b>{ENERGY_LABELS[src]}</b><br>%{{y:.0f}} TWh<extra></extra>'
            ))
    if y0 <= 2011 <= y1:
        fig.add_vline(x=2011, line_dash='dash', line_color=SUBTEXT, line_width=1, opacity=0.6)
        fig.add_annotation(x=2011, y=6500, text='Fukushima — Nuclear collapse',
            showarrow=False, font=dict(color=SUBTEXT, size=10, family=FONT_BODY), xshift=8)
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text='Energy Mix by Source (TWh)', font=dict(color=TEXT, size=14, family=FONT_HEAD)),
        yaxis_title='TWh')
    return fig


@app.callback(
    Output('chart-compare', 'figure'),
    Input('country-dropdown', 'value'),
    Input('year-slider', 'value')
)
def update_compare(selected_countries, year_range):
    y0, y1 = year_range
    fig = go.Figure()

    # Fixed traces: Japan, India, World
    for entity, data, color, dash in [
        ('Japan', japan, RED, 'solid'),
        ('India', india, GREEN, 'dot'),
        ('World', world, BLUE, 'dash')
    ]:
        d = data[(data['year'] >= y0) & (data['year'] <= y1)]
        fig.add_trace(go.Scatter(
            x=d['year'], y=d['co2_per_capita'], mode='lines', name=entity,
            line=dict(color=color, width=2.5, dash=dash),
            hovertemplate=f'<b>{entity} %{{x}}</b><br>%{{y:.2f}} tCO₂/person<extra></extra>'
        ))

    # Dynamic traces from dropdown
    extra_colors = ['#9B59B6','#E67E22','#1ABC9C','#E91E63',
                    '#FF5722','#607D8B','#795548','#FFC107']
    if selected_countries:
        for i, country in enumerate(selected_countries):
            d = df[(df['country'] == country) & (df['year'] >= y0) & (df['year'] <= y1)]
            if not d.empty:
                fig.add_trace(go.Scatter(
                    x=d['year'], y=d['co2_per_capita'], mode='lines', name=country,
                    line=dict(color=extra_colors[i % len(extra_colors)], width=2, dash='dashdot'),
                    hovertemplate=f'<b>{country} %{{x}}</b><br>%{{y:.2f}} tCO₂/person<extra></extra>'
                ))

    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text='Per Capita CO₂: Japan vs India vs World + Selected Countries',
                   font=dict(color=TEXT, size=14, family=FONT_HEAD)),
        yaxis_title='tCO₂/person')
    return fig
@app.callback(
    Output('chart-donut', 'figure'),
    Input('country-dropdown', 'value')
)
def update_donut(selected_countries):
    all_countries = selected_countries or []
    donut_countries = ['Japan'] + [c for c in all_countries if c not in ('World', 'India')]
    
    extra_colors = ['#9B59B6','#E67E22','#1ABC9C','#E91E63',
                    '#FF5722','#607D8B','#795548','#FFC107']
    donut_colors = [RED] + extra_colors[:len(donut_countries)-1]

    shares, labels, colors_final = [], [], []
    for i, country in enumerate(donut_countries):
        src = japan if country == 'Japan' else df[df['country'] == country]
        row = src[src['year'] == 2023]
        if not row.empty and not pd.isna(row['co2_share'].values[0]):
            shares.append(round(row['co2_share'].values[0], 2))
            labels.append(country)
            colors_final.append(donut_colors[i])

    # ── THE FIX: sum all countries before appending Rest of World
    combined_share = round(sum(shares), 2)
    is_coalition   = len(labels) > 1

    labels.append('Rest of World')
    shares.append(round(max(100 - combined_share, 0), 2))
    colors_final.append(BORDER)

    fig_d = go.Figure(go.Pie(
        labels=labels, values=shares, hole=0.65,
        marker=dict(colors=colors_final),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>%{value:.2f}%<extra></extra>'
    ))

    # Center: big % + small "N countries" subtitle when coalition
    fig_d.add_annotation(
        text=f'<b>{combined_share}%</b>',
        x=0.5, y=0.56 if is_coalition else 0.5,
        showarrow=False,
        font=dict(color=TEXT, size=20, family=FONT_HEAD),
        align='center'
    )
    if is_coalition:
        fig_d.add_annotation(
            text=f'{len(labels) - 1} countries',
            x=0.5, y=0.40,
            showarrow=False,
            font=dict(color=SUBTEXT, size=11, family=FONT_BODY),
            align='center'
        )

    fig_d.update_layout(**PLOTLY_LAYOUT)
    fig_d.update_layout(
        title=dict(
            text='Combined Share of Global CO₂ (2023)' if is_coalition
                 else "Japan's Share of Global CO₂ (2023)",
            font=dict(color=TEXT, size=14, family=FONT_HEAD)
        ),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.1, xanchor='center', x=0.5)
    )
    return fig_d

@app.callback(
    Output('chart-bubble', 'figure'),
    Input('bubble-dropdown', 'value')
)
def update_bubble(selected_countries):
    extra_colors = ['#9B59B6', '#E67E22', '#1ABC9C', '#E91E63',
                    '#FF5722', '#607D8B', '#795548', '#FFC107']
 
    def bubble_size(pop):
        if pd.isna(pop) or pop <= 0:
            return 25
        return min(80, max(20, int(pop / 20_000_000)))
 
    fig = go.Figure()
 
    # Fixed: Japan, India, World — GDP from _gdp_bubble (2023 lookup)
    for name, data, color, label in [
        ('Japan', japan, RED,   'Japan'),
        ('India', india, GREEN, 'India'),
        ('World', world, BLUE,  'World Avg'),
    ]:
        row = data[data['year'] == 2023]
        if row.empty:
            continue
        gdp = _gdp_bubble.get(name)
        co2 = row['co2_per_capita'].values[0]
        pop = row['population'].values[0]
        if gdp is None or pd.isna(co2):
            continue
        fig.add_trace(go.Scatter(
            x=[gdp], y=[co2],
            mode='markers+text', name=label, text=[label],
            textposition='top center',
            textfont=dict(color=TEXT, size=13, family=FONT_HEAD),
            marker=dict(size=bubble_size(pop), color=color, opacity=0.75,
                        line=dict(color='white', width=2)),
            hovertemplate=f'<b>{label}</b><br>GDP: $%{{x:,.0f}}<br>CO₂: %{{y:.2f}} t/person<extra></extra>'
        ))
 
    # Dynamic: selected countries — GDP from _gdp_bubble (210 countries, 2023)
    if selected_countries:
        for i, country in enumerate(selected_countries):
            country_df = df[df['country'] == country]
            if country_df.empty:
                continue
            row = country_df[country_df['year'] == 2023]
            if row.empty:
                row = country_df[country_df['year'] == country_df['year'].max()]
            if row.empty:
                continue
            co2 = row['co2_per_capita'].values[0]
            if pd.isna(co2):
                continue
            gdp = _gdp_bubble.get(country)
            if gdp is None or pd.isna(gdp):
                continue
            pop = row['population'].values[0]
            fig.add_trace(go.Scatter(
                x=[gdp], y=[co2],
                mode='markers+text', name=country, text=[country],
                textposition='top center',
                textfont=dict(color=TEXT, size=13, family=FONT_HEAD),
                marker=dict(
                    size=bubble_size(pop),
                    color=extra_colors[i % len(extra_colors)],
                    opacity=0.75, line=dict(color='white', width=2)
                ),
                hovertemplate=f'<b>{country}</b><br>GDP: $%{{x:,.0f}}<br>CO₂: %{{y:.2f}} t/person<extra></extra>'
            ))
 
    fig.update_layout(**PLOTLY_LAYOUT,
        title=dict(text='Wealth vs Emissions — Bubble size reflects population (2023)',
                   font=dict(color=TEXT, size=14, family=FONT_HEAD)),
        xaxis_title='GDP per Capita (USD)',
        yaxis_title='Per Capita CO₂ (tCO₂/person)',
        height=360, showlegend=True)
    return fig    
    print("✅ Callbacks registered")

# ═══════════════════════════════════════════════════════════════
# CELL 9 — Run
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)