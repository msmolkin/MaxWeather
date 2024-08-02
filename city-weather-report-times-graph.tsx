import React, { useState } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CityWeatherReportTimesGraph = () => {
  const [activeTab, setActiveTab] = useState('Austin');

  const timeToMinutes = (timeStr) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
  };

  const minutesToTime = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
  };

  const parseDate = (dateStr) => {
    const [month, day, year] = dateStr.split('/');
    return new Date(year, month - 1, day).getTime();
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  const generateCityData = (city, data) => {
    return data.map(([date, time]) => ({
      city,
      date: parseDate(date),
      time: timeToMinutes(time),
      label: `${date} ${time}`
    }));
  };

  const cityData = {
    'Austin': generateCityData('Austin', [
      ['6/30/24', '16:35'], ['7/1/24', '16:25'], ['7/2/24', '16:36'],
      ['7/3/24', '16:34'], ['7/4/24', '16:22'], ['7/5/24', '16:29'],
      ['7/6/24', '16:22'], ['7/7/24', '16:25'], ['7/8/24', '16:41'],
      ['7/9/24', '16:37'], ['7/10/24', '16:43'], ['7/11/24', '16:43'],
      ['7/12/24', '16:37'], ['7/13/24', '16:22'], ['7/14/24', '16:40'],
      ['7/15/24', '16:28'], ['7/16/24', '16:35']
    ]),
    'Miami': generateCityData('Miami', [
      ['6/30/24', '16:35'], ['7/1/24', '16:25'], ['7/2/24', '16:40'],
      ['7/3/24', '16:26'], ['7/4/24', '16:22'], ['7/5/24', '16:29'],
      ['7/6/24', '16:22'], ['7/7/24', '16:25'], ['7/8/24', '16:35'],
      ['7/9/24', '16:37'], ['7/10/24', '16:29'], ['7/11/24', '16:26'],
      ['7/12/24', '16:25'], ['7/13/24', '16:22'], ['7/14/24', '16:22'],
      ['7/15/24', '16:21'], ['7/16/24', '16:40']
    ]),
    'New York': generateCityData('New York', [
      ['6/30/24', '16:35'], ['7/1/24', '16:35'], ['7/2/24', '16:36'],
      ['7/3/24', '16:34'], ['7/4/24', '16:36'], ['7/5/24', '16:35'],
      ['7/6/24', '16:35'], ['7/7/24', '16:34'], ['7/8/24', '16:41'],
      ['7/9/24', '16:37'], ['7/10/24', '16:43'], ['7/11/24', '16:43'],
      ['7/12/24', '16:37'], ['7/13/24', '16:46'], ['7/14/24', '16:51'],
      ['7/15/24', '16:44'], ['7/16/24', '16:35']
    ]),
    'Chicago': generateCityData('Chicago', [
      ['6/20/24', '16:35'], ['6/21/24', '16:34'], ['6/22/24', '16:34'],
      ['6/23/24', '16:38'], ['6/24/24', '16:18'], ['6/25/24', '16:00'],
      ['6/26/24', '16:34'], ['6/27/24', '16:34'], ['6/28/24', '16:37'],
      ['6/29/24', '16:36'], ['6/30/24', '16:33'], ['7/1/24', '16:34'],
      ['7/2/24', '16:34'], ['7/3/24', '16:35'], ['7/4/24', '16:33'],
      ['7/5/24', '16:35'], ['7/6/24', '16:34'], ['7/7/24', '16:34'],
      ['7/8/24', '16:44'], ['7/9/24', '16:38'], ['7/10/24', '16:35'],
      ['7/11/24', '16:34'], ['7/12/24', '16:32'], ['7/13/24', '16:36'],
      ['7/14/24', '16:35'], ['7/15/24', '16:38'], ['7/16/24', '16:41']
    ])
  };

  const cityColors = {
    'Austin': '#8884d8',
    'Miami': '#82ca9d',
    'New York': '#ffc658',
    'Chicago': '#ff7300'
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const { label, time } = payload[0].payload;
      return (
        <div className="custom-tooltip" style={{ backgroundColor: 'white', padding: '5px', border: '1px solid #ccc' }}>
          <p>{label}</p>
          <p>Report Time: {minutesToTime(time)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-container" style={{ width: '100%', height: '500px' }}>
      <div className="tabs" style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        {Object.keys(cityData).map(city => (
          <button
            key={city}
            onClick={() => setActiveTab(city)}
            style={{
              padding: '10px 20px',
              backgroundColor: activeTab === city ? cityColors[city] : '#f0f0f0',
              border: 'none',
              margin: '0 5px',
              cursor: 'pointer',
              color: activeTab === city ? 'white' : 'black'
            }}
          >
            {city}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 40 }}>
          <CartesianGrid />
          <XAxis 
            type="number" 
            dataKey="date" 
            name="Date" 
            domain={['dataMin', 'dataMax']}
            tickFormatter={formatDate}
            label={{ value: 'Date', position: 'bottom' }}
          />
          <YAxis 
            type="number" 
            dataKey="time" 
            name="Time" 
            domain={['dataMin - 30', 'dataMax + 30']}
            tickFormatter={minutesToTime}
            label={{ value: 'Report Time', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter 
            name={activeTab} 
            data={cityData[activeTab]} 
            fill={cityColors[activeTab]} 
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CityWeatherReportTimesGraph;
