async function loadDataFromCSV(url) {
    const response = await fetch(url);
    const text = await response.text();
    const rows = text.trim().split("\n").slice(1); // skip header
  
    return rows.map((row) => {
      const [
        timestamp,
        direction,
        support,
        resistance,
        open,
        high,
        low,
        close,
        volume,
      ] = row.split(",");
  
      const parsedSupport = JSON.parse(support);
      const parsedResistance = JSON.parse(resistance);
  
      return {
        timestamp,
        support: parsedSupport[0],       // or use Math.min(...parsedSupport)
        resistance: parsedResistance[0], // or use Math.max(...parsedResistance)
        ohlc: [
          parseFloat(open),
          parseFloat(close),
          parseFloat(low),
          parseFloat(high),
        ],
      };
    });
  }
  
  function calculateMA(dayCount, data) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
      if (i < dayCount) {
        result.push("-");
        continue;
      }
      let sum = 0;
      for (let j = 0; j < dayCount; j++) {
        sum += data[i - j].ohlc[1]; // close price
      }
      result.push(sum / dayCount);
    }
    return result;
  }
  
  async function initChart() {
    const rawData = await loadDataFromCSV("data/tsla.csv");
    const dates = rawData.map((item) => item.timestamp);
    const ohlcData = rawData.map((item) => item.ohlc);
    const supportLine = rawData.map((item) => item.support);
    const resistanceLine = rawData.map((item) => item.resistance);
  
    const myChart = echarts.init(document.getElementById("main"));
    const option = {
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "cross",
          animation: false,
          lineStyle: { color: "#376df4", width: 2, opacity: 1 },
        },
      },
      legend: {
        data: ["Candlestick", "MA5", "MA10", "MA20", "MA30", "Support", "Resistance"],
      },
      grid: [{ left: "3%", right: "4%", bottom: "3%", top: "10%", containLabel: true }],
      xAxis: [{
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#8392A5" } },
      }],
      yAxis: [{
        scale: true,
        axisLine: { lineStyle: { color: "#8392A5" } },
        splitLine: { show: false },
      }],
      dataZoom: [{ type: "inside" }, { textStyle: { color: "#8392A5" } }],
      series: [
        {
          name: "Candlestick",
          type: "candlestick",
          data: ohlcData,
          itemStyle: {
            color: "#FD1050",
            color0: "#0CF49B",
            borderColor: "#FD1050",
            borderColor0: "#0CF49B",
          },
        },
        {
          name: "MA5",
          type: "line",
          data: calculateMA(5, rawData),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 1 },
        },
        {
          name: "MA10",
          type: "line",
          data: calculateMA(10, rawData),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 1 },
        },
        {
          name: "MA20",
          type: "line",
          data: calculateMA(20, rawData),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 1 },
        },
        {
          name: "MA30",
          type: "line",
          data: calculateMA(30, rawData),
          smooth: true,
          showSymbol: false,
          lineStyle: { width: 1 },
        },
        {
          name: "Support",
          type: "line",
          data: supportLine,
          lineStyle: { type: "dashed", color: "#0088ff" },
          showSymbol: false,
        },
        {
          name: "Resistance",
          type: "line",
          data: resistanceLine,
          lineStyle: { type: "dashed", color: "#ff8800" },
          showSymbol: false,
        },
      ],
    };
  
    myChart.setOption(option);
  }
  
  initChart();
  