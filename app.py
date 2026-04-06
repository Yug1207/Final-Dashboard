# ╔══════════════════════════════════════════════════════════════╗
# ║        JAPAN CLIMATE DASHBOARD — JUPYTER NOTEBOOK          ║
# ╚══════════════════════════════════════════════════════════════╝

# ═══════════════════════════════════════════════════════════════
# CELL 1 — Install & Imports
# ═══════════════════════════════════════════════════════════════
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import gc

# ═══════════════════════════════════════════════════════════════
# CELL 3 — Load & Prepare Data 
# ═══════════════════════════════════════════════════════════════
# MUST MATCH GITHUB FILE NAMES EXACTLY
FILE_1 = "Main data file 1.xlsx"
FILE_2 = "Main Data File 2.xlsx"

try:
    df_left = pd.read_excel(FILE_1)
    df_right = pd.read_excel(FILE_2)

    if 'country' in df_right.columns.str.lower():
        df_right = df_right.drop(columns=[c for c in df_right.columns if 'country' in c.lower() or 'year' in c.lower()])

    df_raw = pd.concat([df_left.reset_index(drop=True), df_right.reset_index(drop=True)], axis=1)

    df_raw = df_raw.iloc[:, :17]
    df_raw.columns = [
        'country', 'year', 'co2_total', 'co2_share', 'co2_per_capita',
        'co2_consumption', 'gdp_per_capita', 'population',
        'other_renewables', 'biofuels', 'solar', 'wind',
        'hydropower', 'nuclear', 'gas', 'coal', 'oil'
    ]

    df_raw = df_raw.dropna(subset=['country'])
    df_raw['year'] = pd.to_numeric(df_raw['year'], errors='coerce')
    df = df_raw[df_raw['year'] >= 1990].copy()

    japan = df[df['country'] == 'Japan'].reset_index(drop=True)
    india = df[df['country'] == 'India'].reset_index(drop=True)
    world = df[df['country'] == 'World'].reset_index(drop=True)

    del df_left
    del df_right
    del df_raw
    gc.collect()

except Exception as e:
    print(f"Error loading files: {e}")
    df, japan, india, world = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ════════ BULLETPROOF CALCULATIONS ════════
if not japan.empty and 'co2_total' in japan.columns:
    japan['co2_mt'] = japan['co2_total'] / 1e9
    if all(c in japan.columns for c in ['solar', 'wind', 'hydropower', 'other_renewables']):
        japan['renewables'] = japan['solar'] + japan['wind'] + japan['hydropower'] + japan['other_renewables']

def safe_get(data_frame, year, col_name):
    if data_frame.empty or col_name not in data_frame.columns: 
        return 0
    val = data_frame[data_frame['year'] == year][col_name].values
    return val[0] if len(val) > 0 else 0

co2_2023      = safe_get(japan, 2023, 'co2_mt')
pc_2023       = safe_get(japan, 2023, 'co2_per_capita')
pc_2005       = safe_get(japan, 1990, 'co2_per_capita') 
pct_change    = round(((pc_2023 - pc_2005) / pc_2005) * 100, 1) if pc_2005 != 0 else 0
share_2023    = safe_get(japan, 2023, 'co2_share')
world_pc_2023 = safe_get(world, 2023, 'co2_per_capita')
india_pc_2023 = safe_get(india, 2023, 'co2_per_capita')

# Get GDP safely for the bubble chart to prevent crash
jp_gdp_2023 = safe_get(japan, 2023, 'gdp_per_capita')
in_gdp_2023 = safe_get(india, 2023, 'gdp_per_capita')
wd_gdp_2023 = safe_get(world, 2023, 'gdp_per_capita')

print("✅ Data loaded perfectly!")

# ═══════════════════════════════════════════════════════════════
# CELL 4 — Design Tokens
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
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family=FONT_BODY, color=TEXT, size=12),
    margin=dict(l=40, r=20, t=90, b=40),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=SUBTEXT, size=11),
                orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    xaxis=dict(showgrid=False, color=SUBTEXT, tickfont=dict(color=SUBTEXT), linecolor=BORDER, zeroline=False),
    yaxis=dict(showgrid=True, gridcolor=BORDER, color=SUBTEXT, tickfont=dict(color=SUBTEXT), linecolor='rgba(0,0,0,0)', zeroline=False),
    hoverlabel=dict(bgcolor=CARD_BG, bordercolor=BORDER, font=dict(family=FONT_BODY, color=TEXT))
)

ENERGY_COLORS = {
    'coal':       ('#8B7355', 'rgba(139,115,85,0.75)'),
    'oil':        ('#B8860B', 'rgba(184,134,11,0.75)'),
    'gas':        ('#CD853F', 'rgba(205,133,63,0.75)'),
    'nuclear':    ('#1F456E', 'rgba(31,69,110,0.75)'),
    'renewables': ('#4A6B53', 'rgba(74,107,83,0.75)'),
}
ENERGY_LABELS = {'coal':'Coal','oil':'Oil','gas':'Gas','nuclear':'Nuclear','renewables':'Renewables'}

# ═══════════════════════════════════════════════════════════════
# CELL 5 — Static Charts 
# ═══════════════════════════════════════════════════════════════
fig_total = go.Figure()
if not japan.empty and 'co2_mt' in japan.columns:
    fig_total.add_trace(go.Scatter(
        x=japan['year'], y=japan['co2_mt'], mode='lines',
        line=dict(color=RED, width=3), fill='tozeroy', fillcolor='rgba(217,56,30,0.08)',
        hovertemplate='<b>%{x}</b><br>%{y:.1f} MtCO₂<extra></extra>'
    ))
fig_total.update_layout(**PLOTLY_LAYOUT, title=dict(text='Total CO₂ Emissions (MtCO₂)', font=dict(color=TEXT, size=14, family=FONT_HEAD)))

fig_pc = go.Figure()
if not japan.empty:
    fig_pc.add_trace(go.Scatter(
        x=japan['year'], y=japan['co2_per_capita'], mode='lines',
        line=dict(color=BLUE, width=3), fill='tozeroy', fillcolor='rgba(31,69,110,0.08)',
        hovertemplate='<b>%{x}</b><br>%{y:.2f} tCO₂/person<extra></extra>'
    ))
fig_pc.update_layout(**PLOTLY_LAYOUT, title=dict(text='Per Capita CO₂ Emissions (tCO₂/person)', font=dict(color=TEXT, size=14, family=FONT_HEAD)))

fig_compare = go.Figure()
for entity, data, color, dash in [('Japan',japan,RED,'solid'),('India',india,GREEN,'dot'),('World',world,BLUE,'dash')]:
    if not data.empty:
        fig_compare.add_trace(go.Scatter(
            x=data['year'], y=data['co2_per_capita'], mode='lines', name=entity,
            line=dict(color=color, width=2.5, dash=dash),
            hovertemplate=f'<b>{entity} %{{x}}</b><br>%{{y:.2f}} tCO₂/person<extra></extra>'
        ))
fig_compare.update_layout(**PLOTLY_LAYOUT, title=dict(text='Per Capita CO₂: Japan vs India vs World', font=dict(color=TEXT, size=14, family=FONT_HEAD)))

japan_share = round(share_2023, 2)
fig_donut = go.Figure(go.Pie(
    labels=['Japan','Rest of World'], values=[japan_share, max(0, round(100-japan_share,2))],
    hole=0.65, marker=dict(colors=[RED, BORDER]), textinfo='none'
))
fig_donut.add_annotation(text=f'<b>{japan_share}%</b>', x=0.5, y=0.5, showarrow=False, font=dict(color=TEXT, size=20, family=FONT_HEAD))
fig_donut.update_layout(**PLOTLY_LAYOUT, title=dict(text="Japan's Share of Global CO₂ (2023)", font=dict(color=TEXT, size=14, family=FONT_HEAD)), showlegend=True)

fig_scatter = go.Figure()
if not japan.empty:
    fig_scatter.add_trace(go.Scatter(
        x=japan['gdp_per_capita'], y=japan['co2_per_capita'], mode='markers+text', text=japan['year'].astype(str),
        textposition='top center', textfont=dict(color=SUBTEXT, size=9),
        marker=dict(size=10, color=japan['year'], colorscale=[[0,'#E8D5C4'],[0.5,RED],[1,'#8B1A0A']], showscale=True),
        hovertemplate='<b>%{text}</b><br>GDP: $%{x:,.0f}<br>CO₂: %{y:.2f} t/person<extra></extra>'
    ))
fig_scatter.update_layout(**PLOTLY_LAYOUT, title=dict(text='GDP per Capita vs Per Capita CO₂ (1990–2024)', font=dict(color=TEXT, size=14, family=FONT_HEAD)))

_bar = go.Figure(data=[go.Bar(
    x=['Japan','World Average','India'], y=[pc_2023, world_pc_2023, india_pc_2023],
    marker=dict(color=[RED,BLUE,GREEN], opacity=0.85),
    text=[f'{v:.2f}t' for v in [pc_2023, world_pc_2023, india_pc_2023]], textposition='outside'
)])
_bar.update_layout(**PLOTLY_LAYOUT, title=dict(text='Per Capita CO₂ Comparison (2023)', font=dict(color=TEXT, size=14, family=FONT_HEAD)), showlegend=False)

_bubble = go.Figure(data=[
    go.Scatter(x=[jp_gdp_2023], y=[pc_2023], mode='markers+text', name='Japan', text=['Japan'], textposition='top center',
               marker=dict(size=40, color=RED, opacity=0.75, line=dict(color='white', width=2))),
    go.Scatter(x=[in_gdp_2023], y=[india_pc_2023], mode='markers+text', name='India', text=['India'], textposition='top center',
               marker=dict(size=40, color=GREEN, opacity=0.75, line=dict(color='white', width=2))),
    go.Scatter(x=[wd_gdp_2023], y=[world_pc_2023], mode='markers+text', name='World Avg', text=['World Avg'], textposition='top center',
               marker=dict(size=40, color=BLUE, opacity=0.75, line=dict(color='white', width=2))),
])
_bubble.update_layout(**PLOTLY_LAYOUT, title=dict(text='Wealth vs Emissions (2023)', font=dict(color=TEXT, size=14, family=FONT_HEAD)), height=360)

# ═══════════════════════════════════════════════════════════════
# CELL 6 & 7 — App Layout
# ═══════════════════════════════════════════════════════════════
def kpi_card(title, value, unit, color=RED, trend=None):
    return html.Div([
        html.P(title, style={'color':SUBTEXT,'fontSize':'11px','textTransform':'uppercase','margin':'0 0 8px 0','fontFamily':FONT_BODY}),
        html.Div([
            html.Span(value, style={'color':color,'fontSize':'32px','fontWeight':'700','fontFamily':FONT_HEAD}),
            html.Span(f' {unit}', style={'color':SUBTEXT,'fontSize':'13px','marginLeft':'4px','fontFamily':FONT_BODY}),
        ]),
        html.P(trend or '', style={'color':SUBTEXT,'fontSize':'11px','margin':'6px 0 0 0','fontFamily':FONT_BODY}),
    ], style={'background':CARD_BG,'border':f'1px solid {BORDER}','borderTop':f'2px solid {color}','borderRadius':'8px','padding':'20px','flex':'1'})

def chart_card(fig, gid=None):
    kwargs = {'figure': fig, 'config': {'displayModeBar': False}}
    if gid: kwargs['id'] = gid
    return html.Div(dcc.Graph(**kwargs), style={'background':CARD_BG,'borderRadius':'8px','padding':'8px','border':f'1px solid {BORDER}'})

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div(style={'backgroundColor':BG,'fontFamily':FONT_BODY,'padding':'40px 5%'}, children=[
    html.H1("JAPAN CLIMATE DASHBOARD", style={'fontFamily':FONT_HEAD, 'marginBottom':'40px'}),
    html.Div(style={'display':'flex','gap':'16px','flexWrap':'wrap','marginBottom':'40px'}, children=[
        kpi_card('Total CO₂ Emissions',  f'{co2_2023:.1f}',   'MtCO₂',  RED),
        kpi_card('Per Capita Emissions', f'{pc_2023:.2f}',    't/person',BLUE),
        kpi_card('Change Since 1990',    f'{pct_change}%',    '',        GREEN if pct_change < 0 else RED),
        kpi_card('Global CO₂ Share',     f'{share_2023:.2f}', '%',       YELLOW),
    ]),
    html.Div([
        html.P('FILTER BY YEAR RANGE:'),
        dcc.RangeSlider(id='year-slider', min=1990, max=2024, step=1, value=[1990, 2024],
                        marks={y: str(y) for y in range(1990, 2025, 5)})
    ], style={'marginBottom':'40px', 'background':CARD_BG, 'padding':'20px', 'borderRadius':'8px', 'border':f'1px solid {BORDER}'}),
    
    html.Div(style={'display':'grid','gridTemplateColumns':'1fr 1fr','gap':'24px','marginBottom':'40px'}, children=[
        chart_card(fig_total, gid='chart-total'), chart_card(fig_pc, gid='chart-pc')
    ]),

    html.Div(style={'background':CARD_BG,'padding':'20px','borderRadius':'8px','border':f'1px solid {BORDER}','marginBottom':'40px'}, children=[
        dcc.Dropdown(id='energy-dropdown', options=[{'label':v,'value':k} for k,v in ENERGY_LABELS.items()],
                     value=['coal','oil','gas','nuclear','renewables'], multi=True),
        dcc.Graph(id='chart-energy')
    ]),

    html.Div(style={'background':CARD_BG,'padding':'20px','borderRadius':'8px','border':f'1px solid {BORDER}','marginBottom':'40px'}, children=[
        dcc.Dropdown(id='country-dropdown', 
                     options=[] if df.empty or 'country' not in df.columns else [{'label': c, 'value': c} for c in sorted(df['country'].dropna().unique()) if c not in ['Japan','India','World']],
                     value=[], multi=True, placeholder='Add countries to compare...'),
        html.Div(style={'display':'grid','gridTemplateColumns':'2fr 1fr','gap':'24px','marginTop':'20px'}, children=[
            chart_card(fig_compare, gid='chart-compare'), chart_card(fig_donut, gid='chart-donut')
        ])
    ]),
    
    chart_card(fig_scatter),
    
    html.Div(style={'display':'grid','gridTemplateColumns':'1fr 1fr','gap':'24px','marginTop':'40px'}, children=[
        chart_card(_bar),
        html.Div(style={'background':CARD_BG,'padding':'20px','borderRadius':'8px','border':f'1px solid {BORDER}'}, children=[
            dcc.Dropdown(id='bubble-dropdown', 
                         options=[] if df.empty or 'country' not in df.columns else [{'label': c, 'value': c} for c in sorted(df['country'].dropna().unique()) if c not in ['Japan','India','World']], 
                         value=[], multi=True, placeholder='Add countries to bubble chart...'),
            dcc.Graph(id='chart-bubble', figure=_bubble)
        ])
    ])
])

# ═══════════════════════════════════════════════════════════════
# CELL 8 — Callbacks
# ═══════════════════════════════════════════════════════════════
@app.callback(
    Output('chart-total', 'figure'), Output('chart-pc', 'figure'),
    Input('year-slider', 'value')
)
def update_trends(year_range):
    y0, y1 = year_range
    j = japan[(japan['year'] >= y0) & (japan['year'] <= y1)] if not japan.empty else pd.DataFrame()
    f1, f2 = go.Figure(), go.Figure()
    if not j.empty and 'co2_mt' in j.columns:
        f1.add_trace(go.Scatter(x=j['year'], y=j['co2_mt'], mode='lines', line=dict(color=RED, width=3), fill='tozeroy'))
    if not j.empty:
        f2.add_trace(go.Scatter(x=j['year'], y=j['co2_per_capita'], mode='lines', line=dict(color=BLUE, width=3), fill='tozeroy'))
    f1.update_layout(**PLOTLY_LAYOUT, title='Total CO₂ Emissions (MtCO₂)')
    f2.update_layout(**PLOTLY_LAYOUT, title='Per Capita CO₂ Emissions')
    return f1, f2

@app.callback(
    Output('chart-energy', 'figure'),
    Input('energy-dropdown', 'value'), Input('year-slider', 'value')
)
def update_energy(selected, year_range):
    y0, y1 = year_range
    j = japan[(japan['year'] >= y0) & (japan['year'] <= y1)] if not japan.empty else pd.DataFrame()
    fig = go.Figure()
    if selected and not j.empty:
        for src in selected:
            if src in j.columns:
                lc, fc = ENERGY_COLORS[src]
                fig.add_trace(go.Scatter(x=j['year'], y=j[src], mode='lines', name=ENERGY_LABELS[src], stackgroup='one', line=dict(color=lc), fillcolor=fc))
    fig.update_layout(**PLOTLY_LAYOUT, title='Energy Mix by Source (TWh)')
    return fig

@app.callback(
    Output('chart-compare', 'figure'), Output('chart-donut', 'figure'),
    Input('country-dropdown', 'value'), Input('year-slider', 'value')
)
def update_compare(selected_countries, year_range):
    y0, y1 = year_range
    fig = go.Figure()
    for entity, data, color, dash in [('Japan', japan, RED, 'solid'), ('India', india, GREEN, 'dot'), ('World', world, BLUE, 'dash')]:
        if not data.empty:
            d = data[(data['year'] >= y0) & (data['year'] <= y1)]
            fig.add_trace(go.Scatter(x=d['year'], y=d['co2_per_capita'], mode='lines', name=entity, line=dict(color=color, width=2.5, dash=dash)))
    
    extra_colors = ['#9B59B6','#E67E22','#1ABC9C','#E91E63','#FF5722','#607D8B','#795548','#FFC107']
    shares, labels, colors_final = [], [], []
    
    # Base donut config for Japan
    jp_share_val = safe_get(japan, 2023, 'co2_share')
    if jp_share_val > 0:
        shares.append(jp_share_val)
        labels.append('Japan')
        colors_final.append(RED)

    if selected_countries:
        for i, country in enumerate(selected_countries):
            d = df[(df['country'] == country)]
            d_filtered = d[(d['year'] >= y0) & (d['year'] <= y1)]
            if not d_filtered.empty:
                fig.add_trace(go.Scatter(x=d_filtered['year'], y=d_filtered['co2_per_capita'], mode='lines', name=country, line=dict(color=extra_colors[i % len(extra_colors)], width=2, dash='dashdot')))
            
            c_share_val = safe_get(d, 2023, 'co2_share')
            if c_share_val > 0:
                shares.append(c_share_val)
                labels.append(country)
                colors_final.append(extra_colors[i % len(extra_colors)])

    fig.update_layout(**PLOTLY_LAYOUT, title='Per Capita CO₂ Comparison')

    combined_share = round(sum(shares), 2)
    labels.append('Rest of World')
    shares.append(max(0, round(100 - combined_share, 2)))
    colors_final.append(BORDER)
    
    fig_d = go.Figure(go.Pie(labels=labels, values=shares, hole=0.65, marker=dict(colors=colors_final), textinfo='none'))
    fig_d.add_annotation(text=f'<b>{combined_share}%</b>', x=0.5, y=0.5, showarrow=False, font=dict(color=TEXT, size=20))
    fig_d.update_layout(**PLOTLY_LAYOUT, title='Combined Share of Global CO₂ (2023)', showlegend=True)
    
    return fig, fig_d

@app.callback(
    Output('chart-bubble', 'figure'),
    Input('bubble-dropdown', 'value')
)
def update_bubble(selected_countries):
    fig = go.Figure()
    extra_colors = ['#9B59B6', '#E67E22', '#1ABC9C', '#E91E63', '#FF5722', '#607D8B', '#795548', '#FFC107']

    for name, data, color in [('Japan', japan, RED), ('India', india, GREEN), ('World', world, BLUE)]:
        if data.empty: continue
        row = data[data['year'] == 2023]
        if not row.empty and 'gdp_per_capita' in row.columns and 'co2_per_capita' in row.columns:
            gdp = row['gdp_per_capita'].values[0]
            co2 = row['co2_per_capita'].values[0]
            if not pd.isna(gdp) and not pd.isna(co2):
                fig.add_trace(go.Scatter(x=[gdp], y=[co2], mode='markers+text', name=name, text=[name], textposition='top center',
                                         marker=dict(size=40, color=color, opacity=0.75)))

    if selected_countries:
        for i, country in enumerate(selected_countries):
            c_df = df[df['country'] == country]
            if c_df.empty: continue
            row = c_df[c_df['year'] == 2023]
            if not row.empty and 'gdp_per_capita' in row.columns and 'co2_per_capita' in row.columns:
                gdp = row['gdp_per_capita'].values[0]
                co2 = row['co2_per_capita'].values[0]
                if not pd.isna(gdp) and not pd.isna(co2):
                    fig.add_trace(go.Scatter(x=[gdp], y=[co2], mode='markers+text', name=country, text=[country], textposition='top center',
                                             marker=dict(size=30, color=extra_colors[i % len(extra_colors)], opacity=0.75)))

    fig.update_layout(**PLOTLY_LAYOUT, title='Wealth vs Emissions (2023)', xaxis_title='GDP per Capita', yaxis_title='CO₂ per Capita', height=360)
    return fig

# ═══════════════════════════════════════════════════════════════
# CELL 9 — Run
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)