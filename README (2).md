# Japan's Climate Shift: A 35-Year Data Story (1990-2024)

An interactive dashboard that tracks how Japan's carbon emissions and energy mix changed over 35 years, and asks a harder question: how does Japan's footprint compare with the rest of the world?

**Live dashboard:**(https://final-dashboard-three.vercel.app/)

## What this project is

I built this for the course *Climate Change, Sustainability and Development* in the BS in Analytics and Sustainability Studies at TISS Mumbai. The goal was to take raw emissions and energy data and turn it into something a non-technical reader can explore, not just a set of static charts.

The dashboard follows one story: Japan cut its emissions after 2013, but it still emits far more per person than the world average and far more than India. The charts let you check that for yourself.

## What you can do in the dashboard

- **Read the headline numbers.** Total CO2, per capita CO2, change since 1990 and Japan's share of global emissions, shown as summary cards.
- **Filter by year.** A range slider updates the trend and energy charts together.
- **Follow the emissions trend.** Total and per capita CO2 over time, with the 2011 Fukushima disaster and the 2016 Paris Agreement marked.
- **See the energy transition.** A stacked area chart of coal, oil, gas, nuclear and renewables. Pick any combination of sources from the dropdown.
- **Compare countries.** Per capita CO2 for Japan, India and the world, plus any other countries you add. A donut chart shows the combined share of global emissions for whatever you select.
- **Test the decoupling idea.** A scatter plot of GDP per capita against CO2 per capita, one point per year, to see whether economic growth and emissions moved apart.
- **Explore climate justice.** A per capita comparison and a bubble chart of wealth vs emissions, with bubble size showing population. You can add more countries to the bubble chart.

## What the data shows

These numbers come straight from the dataset behind the dashboard.

- Japan's total CO2 peaked at about **1,312 MtCO2 in 2013** and fell to about **987 MtCO2 in 2023**.
- Nuclear energy dropped from about **761 TWh in 2010 to 37 TWh in 2013** after Fukushima, and had only recovered to about **189 TWh by 2023**. Over the same period, fossil fuel use stayed high.
- Per capita emissions went from **9.36 t in 1990** to a peak of **10.27 t in 2013**, then down to **7.94 t in 2023**. That is still about 1.7 times the world average (4.71 t) and about 3.7 times India's (2.13 t).
- Japan's share of global CO2 fell from **5.1% in 1990 to 2.6% in 2023**, while India's rose from **2.5% to 8.0%**.

## Data sources

- Our World in Data, *CO2 and Greenhouse Gas Emissions* (2024): https://ourworldindata.org/co2-emissions
- Our World in Data, *Energy Mix* (2024): https://ourworldindata.org/energy-mix
- World Bank, *GDP per Capita* (2024): https://data.worldbank.org

All three sources are combined in one Excel file, `Main data for Assignment.xlsx`, which covers 1990 to 2024.

## Built with

- **Python** for data cleaning and the app logic
- **pandas** and **openpyxl** to read and reshape the Excel data
- **Plotly** for the charts
- **Dash** and **dash-bootstrap-components** for the interactive web app
- **Vercel** for hosting

## Project structure

```
Final-Dashboard/
├── app.py                           # The whole app: data loading, charts, layout, callbacks
├── Main data for Assignment.xlsx    # Combined dataset (OWID + World Bank)
├── requirements.txt                 # Python dependencies
└── Procfile                         # Process file for hosts like Render or Heroku
```

## Run it on your own computer

1. Clone the repo and open the folder:
   ```
   git clone https://github.com/Yug1207/Final-Dashboard.git
   cd Final-Dashboard
   ```
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the app:
   ```
   python app.py
   ```
4. Open http://localhost:8050 in your browser.




## Author

**Yug**, student at TISS Mumbai, BS in Analytics and Sustainability Studies (2024-28).
GitHub: [Yug1207](https://github.com/Yug1207)
