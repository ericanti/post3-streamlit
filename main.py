import streamlit as st
import pandas as pd
import altair as alt

# load data with caching
@st.cache_data
def load_data():
    billboard = pd.read_csv("merged_data.csv")
    return billboard

merged_data = load_data()

# sidebar filters
st.sidebar.header("Global Filters")
selected_years = st.sidebar.multiselect(
    "Select Years",
    options=[1969, 2019],
    default=[1969, 2019]
)

selected_genres = st.sidebar.multiselect(
    "Filter Genres",
    options=merged_data['genre_full'].unique(),
    default=merged_data['genre_full'].unique()
)

min_weeks = st.sidebar.slider(
    "Minimum Weeks on Chart",
    min_value=0,
    max_value=int(merged_data['weeks_on_chart'].max()),
    value=0
)

# filter data based on selections
filtered_data = merged_data[
    (merged_data['year'].isin(selected_years)) &
    (merged_data['genre_full'].isin(selected_genres)) &
    (merged_data['weeks_on_chart'] >= min_weeks)
]

# app layout
st.title("Billboard Top Hits Analysis (1969-2019)")
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", 
    "😊 Mood Analysis", 
    "👫 Gender Trends", 
    "🎵 Custom Analysis"
])

with tab1:
    st.header("Data Overview")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Songs Analyzed", filtered_data.shape[0])
    with col2:
        avg_weeks = filtered_data['weeks_on_chart'].mean()
        st.metric("Average Weeks on Chart", f"{avg_weeks:.1f} weeks")
    
    st.subheader("Genre Proportions by Year")
    
    # genre proportions chart
    genre_chart = alt.Chart(filtered_data).transform_aggregate(
        count='count()',
        groupby=['year', 'genre_full']
    ).transform_joinaggregate(
        total='sum(count)',
        groupby=['year']
    ).transform_calculate(
        proportion='datum.count / datum.total'
    ).mark_bar().encode(
        x=alt.X('genre_full:N', title='Genre', 
               axis=alt.Axis(labelAngle=-45, labelOverlap=False)),
        y=alt.Y('proportion:Q', title='Proportion', axis=alt.Axis(format='%')),
        color='year:N',
        column=alt.Column('year:N', spacing=10),
        tooltip=[
            alt.Tooltip('genre_full:N', title='Genre'),
            alt.Tooltip('proportion:Q', title='Proportion', format='.1%'),
            'year:N'
        ]
    ).properties(
        width=400,
        height=400
    )
    st.altair_chart(genre_chart)

with tab2:
    st.header("Song Mood Analysis")
    
    mood_view = st.radio(
        "Comparison View",
        ["Year Comparison", "Genre Breakdown"],
        horizontal=True
    )
    
    if mood_view == "Year Comparison":
        # proportion of happy songs per year
        year_stats = (
            filtered_data
            .groupby('year')['mood_happy']
            .apply(lambda x: (x == 'happy').mean())
            .reset_index(name='proportion_happy')
        )
        
        chart = alt.Chart(year_stats).mark_bar().encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('proportion_happy:Q', title='Proportion Happy', axis=alt.Axis(format='%')),
            color='year:N',
            tooltip=[
                alt.Tooltip('year:O', title='Year'),
                alt.Tooltip('proportion_happy:Q', title='Happy %', format='.1%')
            ]
        ).properties(
            width=600,
            height=400,
            title="Proportion of Happy Songs by Year"
        )
    else:
        # proportion of happy songs per genre per year
        genre_stats = (
            filtered_data
            .groupby(['genre_full', 'year'])['mood_happy']
            .apply(lambda x: (x == 'happy').mean())
            .reset_index(name='proportion_happy')
        )
        
        # base chart
        base = alt.Chart(genre_stats).mark_bar().encode(
            x=alt.X('genre_full:N', 
                   title='Genre', 
                   axis=alt.Axis(labelAngle=-45, labelOverlap=False)),
            y=alt.Y('proportion_happy:Q', 
                   title='Proportion Happy', 
                   axis=alt.Axis(format='%')),
            color='year:N',
            tooltip=[
                alt.Tooltip('genre_full:N', title='Genre'),
                alt.Tooltip('year:O', title='Year'),
                alt.Tooltip('proportion_happy:Q', title='Happy %', format='.1%')
            ]
        ).properties(
            width=400,
            height=350
        )
        
        # faceted chart
        chart = base.facet(
            column=alt.Column('year:N', header=alt.Header(title='Year')),
            spacing=20
        ).properties(
            title="Happy Songs by Genre and Year"
        )
    
    st.altair_chart(chart, use_container_width=True)

with tab3:
    st.header("Artist Gender Trends")

    # ender proportions
    gender_prop = alt.Chart(filtered_data).transform_aggregate(
        count='count()',
        groupby=['year', 'gender']
    ).transform_joinaggregate(
        total='sum(count)',
        groupby=['year']
    ).transform_calculate(
        proportion='datum.count / datum.total'
    ).mark_bar().encode(
        x='year:O',
        y=alt.Y('proportion:Q', axis=alt.Axis(format='%')),
        color='gender:N',
        tooltip=['year', 'gender', alt.Tooltip('proportion:Q', format='.1%')]
    ).properties(
        title="Gender Proportions by Year",
        width=700,
        height=350
    )
    st.altair_chart(gender_prop)

    # weeks by gender boxplot
    gender_weeks = alt.Chart(filtered_data).mark_boxplot(size=60).encode(
        x='gender:N',
        y='weeks_on_chart:Q',
        color='gender:N',
        tooltip=['median(weeks_on_chart):Q']
    ).properties(
        title="Weeks on Chart by Gender",
        width=700,
        height=350
    )
    st.altair_chart(gender_weeks)

with tab4:
    st.header("Custom Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        x_axis = st.selectbox("X-axis", options=['peak_position', 'weeks_on_chart', 'bpm'])
        hue_var = st.selectbox("Color by", options=['mood_happy', 'gender', 'year'])
    with col2:
        y_axis = st.selectbox("Y-axis", options=['weeks_on_chart', 'peak_position', 'loudness'])
        filter_year = st.checkbox("Split by Year")
    
    # base chart with conditional sizing
    if filter_year:
        # smaller dimensions for split view
        base_chart = alt.Chart(filtered_data).properties(
            width=350,
            height=250
        )
    else:
        # larger dimensions for single view
        base_chart = alt.Chart(filtered_data).properties(
            width=700,
            height=400
        )
    
    chart = base_chart.mark_circle(size=40).encode(
        x=alt.X(x_axis, title=x_axis.replace('_', ' ').title()),
        y=alt.Y(y_axis, title=y_axis.replace('_', ' ').title()),
        color=f'{hue_var}:N',
        tooltip=[x_axis, y_axis, 'song', 'artist', 'genre_full', 'year']
    ).interactive()
    
    if filter_year:
        chart = chart.facet(column='year:N')
    
    st.altair_chart(chart)

# add instructions and info in sidebar
with st.sidebar.expander("How to Use"):
    st.write("""
    1. Use global filters to adjust dataset
    2. Explore different tabs for various analyses
    3. Customize visualizations in the Custom Analysis tab
    """)

st.sidebar.info("Explore musical trends between 1969 and 2019!")