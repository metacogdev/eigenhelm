function createTemperatureLog() {
  var readings = [];

  function addReading(temp, timestamp) {
    readings.push({ temp: temp, timestamp: timestamp });
  }

  function getAverage() {
    if (readings.length === 0) return 0;
    var sum = 0;
    for (var i = 0; i < readings.length; i++) {
      sum += readings[i].temp;
    }
    return sum / readings.length;
  }

  function getMax() {
    if (readings.length === 0) return null;
    var max = readings[0].temp;
    for (var i = 1; i < readings.length; i++) {
      if (readings[i].temp > max) {
        max = readings[i].temp;
      }
    }
    return max;
  }

  function getMin() {
    if (readings.length === 0) return null;
    var min = readings[0].temp;
    for (var i = 1; i < readings.length; i++) {
      if (readings[i].temp < min) {
        min = readings[i].temp;
      }
    }
    return min;
  }

  function getReadingCount() {
    return readings.length;
  }

  return {
    addReading: addReading,
    getAverage: getAverage,
    getMax: getMax,
    getMin: getMin,
    getReadingCount: getReadingCount,
  };
}
