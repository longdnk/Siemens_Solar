myArr = []
myLabels = []

myDayArr = []
myDayLabels = []

function addValue(x) {
    myArr.push(x);
    console.log(x);
}

function addDate(y) {
    myLabels.push(y);
    console.log(y);
}
function clearDateAndValue(){
    myArr = []
    myLabels = []
}
// bar chart
function showBarChart() {
    //save energy values and date in new variables
    myDayArr = myArr
    myDayLabels = myLabels

    const ctx = document.getElementById('canvas').getContext('2d');
    const myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            //labels: ['1 star', '2 star', '3 star', '4 star', '5 star'],
            labels: myLabels,
            datasets: [{
                label: 'Hide',
                //data: [33543, 24847, 34222, 76592, 40796],
                data: myArr,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    //'rgba(255, 206, 86, 0.2)',
                    'rgba(254, 255, 31, 1)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false,
                }
            },
            title: {
                display: true,
                text: "Degree for hour",
                fontSize: 28
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        // Include a dollar sign in the ticks
                        callback: function (value, index, values) {
                            return value + " KWh";
                        }
                    }
                }
            }
        }
    });
}

// Line chart
function showLineChart() {
    let myChart = document.getElementById('LineChart').getContext('2d');
    let masspopCHart = new Chart(myChart, {
        type: 'line',
        data: {
            labels: myLabels,
            datasets: [{
                label: 'Hide',
                data: myArr,
                fill: true,
                lineTension: 0.5,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    // 'rgba(255, 206, 86, 0.2)',
                    'rgba(254, 255, 31, 1)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)',
                    'rgba(255, 159, 64, 0.2)',
                    'rgba(255, 159, 64, 0.2)',
                ],
                borderWidth: 4,
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false,
                }
            },
            title: {
                display: true,
                // text: "rating in pie chart",
                fontSize: 18
            },
            scales: {
                x: {},
                y: {
                    ticks: {
                        // Include a dollar sign in the ticks
                        callback: function (value, index, values) {
                            return value + " KWh";
                        }
                    }
                }
            },
        }
    });
}

function showAll() {
    showBarChart();
    showLineChart()
}

exportToCsv = function () {
    result = []
    for (let i = 0; i < myDayArr.length; ++i) {
        result.push("\r\n" + myDayLabels[i] + ", " + myDayArr[i])
    }
    var Results = [
        result,
    ];
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
    var yyyy = today.getFullYear();
    var res = document.getElementById("result").innerHTML;
    const maximum = document.getElementById("maximum").innerHTML;
    const minimum = document.getElementById("minimum").innerHTML;
    const avg = document.getElementById("avg").innerHTML;
    const sum = document.getElementById("total").innerHTML;
    today = dd + '/' + mm + '/' + yyyy;
    var CsvString = "";
    CsvString += "Export date " + today + "\n";
    CsvString += res + ": " + sum + "\n";
    CsvString += "Maximum power: " + maximum + "\n" + "Minimum power: " + minimum + "\n" + "Average power: " + avg + "\n";
    CsvString += 'Date' + ',' + 'kWh'
    Results.forEach(function (RowItem, RowIndex) {
        RowItem.forEach(function (ColItem, ColIndex) {
            CsvString += ColItem + ',';
        });
        CsvString += "\r\n";
    });
    CsvString = "data:application/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(CsvString);
    var x = document.createElement("A");
    x.setAttribute("href", CsvString);
    x.setAttribute("download", "Solar_Energy_Prediction" + ".csv");
    document.body.appendChild(x);
    x.click();
}

function PDFexport(id, title) {
    const canvas = document.getElementById(id);
    const img = canvas.toDataURL('img/jpeg', 1.0);
    console.log(img);
    let pdf = new jsPDF();
    pdf.setFontSize(20);
    pdf.addImage(img, 'JPEG', 5, 5, 200, 180);
    pdf.text(15, 15, title);
    pdf.save(title + '.pdf');
}

function toggleTheResults() {
     const x = document.getElementById("myDIV");
     const y = document.getElementById("toggleBtn");
     if (x.style.display === "none") {
        x.style.display = "block";
        y.innerHTML = "Hide details";
     }
     else {
        x.style.display = "none";
        y.innerHTML = "Show details";
     }
}

function backHome() {
    window.location.replace("/index.html");
}