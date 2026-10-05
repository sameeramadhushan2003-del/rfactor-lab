import { useEffect, useMemo, useState } from "react";

import { motion } from "framer-motion";



import {

  ResponsiveContainer,

  LineChart,

  Line,

  XAxis,

  YAxis,

  CartesianGrid,

  Tooltip,

  ReferenceLine,

  Legend,

  BarChart,

  Bar,

} from "recharts";



import {

  Activity,

  ArrowDownRight,

  BarChart3,

  Gauge,

  RefreshCw,

  TriangleAlert,

  WalletCards,

} from "lucide-react";





const TEST_NAMES = {

  Validation6: "Validation",

  FinalTime20: "Time Holdout",

  FinalAsset3: "Asset Holdout",

};





function Execution() {



  const [data, setData] = useState(null);

  const [timeseries, setTimeseries] = useState([]);

  const [selectedCost, setSelectedCost] = useState(2.5);

  const [selectedTest, setSelectedTest] = useState("FinalTime20");





  useEffect(() => {

    Promise.all([
      fetch("/data/research.json").then((response) => {
        if (!response.ok) {
          throw new Error("Could not load research.json");
        }

        return response.json();
      }),

      fetch("/data/backtest_timeseries.json").then((response) => {
        if (!response.ok) {
          throw new Error("Could not load backtest_timeseries.json");
        }

        return response.json();
      }),
    ])
      .then(([researchResult, timeseriesResult]) => {
        setData(researchResult);
        setTimeseries(timeseriesResult);
      })
      .catch((error) => {
        console.error(
          "Failed to load backtest data:",
          error
        );
      });

  }, []);





  const execution =

    data?.execution ?? [];





  const currentResults = useMemo(() => {



    return execution

      .filter(

        (row) =>

          Number(row.costBps) ===

          Number(selectedCost)

      )

      .map((row) => ({

        ...row,

        displayName:

          TEST_NAMES[row.test] ??

          row.test,

      }));



  }, [

    execution,

    selectedCost,

  ]);





  const costChart = useMemo(() => {



    const costs = [

      ...new Set(

        execution.map(

          (item) =>

            item.costBps

        )

      ),

    ].sort(

      (a, b) =>

        a - b

    );





    return costs.map(

      (cost) => {



        const point = {

          cost,

        };





        execution

          .filter(

            (row) =>

              row.costBps === cost

          )

          .forEach(

            (row) => {



              point[

                TEST_NAMES[

                  row.test

                ] ?? row.test

              ] =

                row.returnPct;



            }

          );





        return point;



      }

    );



  }, [execution]);





  const selectedTestRows = useMemo(() => {

    return timeseries
      .filter(
        (row) =>
          row.test === selectedTest
      )
      .sort(
        (a, b) =>
          new Date(a.datetime) -
          new Date(b.datetime)
      );

  }, [
    timeseries,
    selectedTest,
  ]);


  const equityChart = useMemo(() => {

    const points = new Map();

    selectedTestRows.forEach((row) => {

      const datetime = row.datetime;

      if (!points.has(datetime)) {
        points.set(datetime, {
          datetime,
        });
      }

      const point = points.get(datetime);
      const cost = Number(row.costBps);

      if (cost === 0) {
        point.equity0 = Number(row.equity);
      }

      if (cost === 2.5) {
        point.equity2_5 = Number(row.equity);
      }

      if (cost === 5) {
        point.equity5 = Number(row.equity);
      }

      if (cost === 10) {
        point.equity10 = Number(row.equity);
      }

    });

    return [...points.values()];

  }, [selectedTestRows]);


  const drawdownChart = useMemo(() => {

    return selectedTestRows
      .filter(
        (row) =>
          Number(row.costBps) ===
          Number(selectedCost)
      )
      .map((row) => ({
        datetime: row.datetime,
        drawdownPct:
          Number(row.drawdownPct),
      }));

  }, [
    selectedTestRows,
    selectedCost,
  ]);


  const formatBacktestDate = (value) => {

    const date = new Date(value);

    return date.toLocaleDateString(
      undefined,
      {
        month: "short",
        day: "numeric",
      }
    );

  };


  if (!data) {



    return (

      <div className="validation-loading">

        Loading execution research...

      </div>

    );



  }





  const finalTime =

    currentResults.find(

      (item) =>

        item.test ===

        "FinalTime20"

    );





  const assetHoldout =

    currentResults.find(

      (item) =>

        item.test ===

        "FinalAsset3"

    );





  const validation =

    currentResults.find(

      (item) =>

        item.test ===

        "Validation6"

    );





  return (



    <motion.div

      className="execution-page"

      initial={{

        opacity: 0,

        y: 20,

      }}

      animate={{

        opacity: 1,

        y: 0,

      }}

      transition={{

        duration: 0.5,

      }}

    >



      {/* HEADER */}



      <section className="execution-header">



        <div className="execution-header-copy">



          <div className="hero-badge">



            <span className="badge-dot"></span>



            HISTORICAL BACKTEST



          </div>





          <h1>



            Signal strength

            <br />



            meets



            <span>

              {" "}friction.

            </span>



          </h1>





          <p>



            The validated reversal factor produces

            positive gross returns, but frequent

            portfolio rebalancing creates substantial

            transaction-cost sensitivity.



          </p>





          <div className="execution-rule-row">



            <RulePill

              label="Signal"

              value="1H Reversal"

            />



            <RulePill

              label="Long"

              value="Bottom 25%"

            />



            <RulePill

              label="Short"

              value="Top 25%"

            />



            <RulePill

              label="Turnover Cap"

              value="0.50"

            />

            <RulePill

              label="Rebalance"

              value="1 Hour"

            />



          </div>



        </div>





        <motion.div

          className="execution-warning-card"

          initial={{

            opacity: 0,

            scale: 0.94,

          }}

          animate={{

            opacity: 1,

            scale: 1,

          }}

          transition={{

            delay: 0.2,

          }}

        >



          <div className="warning-icon">



            <TriangleAlert

              size={27}

            />



          </div>





          <span>

            IMPLEMENTATION STATUS

          </span>





          <h2>

            COST-SENSITIVE

          </h2>





          <p>



            Predictive power survives holdout

            testing, but net profitability depends

            strongly on trading friction.



          </p>





          <div className="execution-warning-bottom">



            <RefreshCw

              size={15}

            />



            High-frequency rebalancing is

            the primary limitation.



          </div>



        </motion.div>



      </section>





      {/* COST SELECTOR */}



      <section className="content-section execution-content">



        <div className="execution-section-title">



          <div>



            <span className="eyebrow">

              COST SCENARIO

            </span>



            <h2>

              Transaction-cost sensitivity

            </h2>



          </div>





          <div className="cost-selector">



            {[0, 2.5, 5, 10].map(

              (cost) => (



                <button

                  key={cost}

                  className={

                    selectedCost === cost

                      ? "cost-button active"

                      : "cost-button"

                  }

                  onClick={() =>

                    setSelectedCost(cost)

                  }

                >



                  {cost} bps



                </button>



              )

            )}



          </div>



        </div>





        {/* METRICS */}



        <div className="execution-metrics">



          <ExecutionMetric

            icon={BarChart3}

            label="Validation Return"

            value={

              validation

                ? `${validation.returnPct.toFixed(2)}%`

                : "—"

            }

            negative={

              validation?.returnPct < 0

            }

            detail="6 validation assets"

            delay={0}

          />





          <ExecutionMetric

            icon={Activity}

            label="Time Holdout"

            value={

              finalTime

                ? `${finalTime.returnPct.toFixed(2)}%`

                : "—"

            }

            negative={

              finalTime?.returnPct < 0

            }

            detail="20 assets · future 65 days"

            delay={0.1}

          />





          <ExecutionMetric

            icon={WalletCards}

            label="Asset Holdout"

            value={

              assetHoldout

                ? `${assetHoldout.returnPct.toFixed(2)}%`

                : "—"

            }

            negative={

              assetHoldout?.returnPct < 0

            }

            detail="AMD · GLW · META"

            delay={0.2}

          />





          <ExecutionMetric

            icon={RefreshCw}

            label="Avg Turnover"

            value={

              finalTime

                ? finalTime.turnover.toFixed(2)

                : "—"

            }

            detail="Hourly turnover cap"

            delay={0.3}

          />



        </div>





        {/* ACTUAL BACKTEST PATH */}

        <div className="backtest-path-header">

          <div>

            <span className="eyebrow">
              ACTUAL BACKTEST PATH
            </span>

            <h2>
              Equity and drawdown
            </h2>

            <p>
              Curves reconstructed from the frozen
              turnover-capped hourly portfolio.
            </p>

          </div>


          <div className="backtest-test-selector">

            {Object.entries(TEST_NAMES).map(
              ([testKey, testLabel]) => (

                <button
                  key={testKey}
                  className={
                    selectedTest === testKey
                      ? "backtest-test-button active"
                      : "backtest-test-button"
                  }
                  onClick={() =>
                    setSelectedTest(testKey)
                  }
                >
                  {testLabel}
                </button>

              )
            )}

          </div>

        </div>


        <div className="backtest-path-grid">

          <motion.div
            className="research-chart-card backtest-equity-card"
            initial={{
              opacity: 0,
              y: 20,
            }}
            whileInView={{
              opacity: 1,
              y: 0,
            }}
            viewport={{
              once: true,
            }}
          >

            <div className="chart-card-header">

              <div>

                <span className="eyebrow">
                  CUMULATIVE EQUITY
                </span>

                <h3>
                  Portfolio equity by cost scenario
                </h3>

              </div>

              <div className="chart-note">
                Start = 1.00
              </div>

            </div>


            <ResponsiveContainer
              width="100%"
              height={390}
            >

              <LineChart data={equityChart}>

                <CartesianGrid
                  strokeDasharray="4 4"
                  stroke="rgba(255,255,255,0.045)"
                  vertical={false}
                />

                <XAxis
                  dataKey="datetime"
                  minTickGap={45}
                  tickFormatter={formatBacktestDate}
                  tick={{
                    fill: "#737d96",
                    fontSize: 10,
                  }}
                  axisLine={false}
                  tickLine={false}
                />

                <YAxis
                  domain={["auto", "auto"]}
                  tickFormatter={(value) =>
                    Number(value).toFixed(2)
                  }
                  tick={{
                    fill: "#59647d",
                    fontSize: 10,
                  }}
                  axisLine={false}
                  tickLine={false}
                />

                <Tooltip
                  labelFormatter={formatBacktestDate}
                  contentStyle={{
                    background: "#111827",
                    border:
                      "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "10px",
                  }}
                  formatter={(value, name) => [
                    Number(value).toFixed(4),
                    name,
                  ]}
                />

                <Legend />

                <ReferenceLine
                  y={1}
                  stroke="rgba(255,255,255,0.16)"
                />

                <Line
                  type="monotone"
                  dataKey="equity0"
                  name="0 bps"
                  stroke="#3ee2aa"
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />

                <Line
                  type="monotone"
                  dataKey="equity2_5"
                  name="2.5 bps"
                  stroke="#63c7ff"
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />

                <Line
                  type="monotone"
                  dataKey="equity5"
                  name="5 bps"
                  stroke="#8d79ff"
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />

                <Line
                  type="monotone"
                  dataKey="equity10"
                  name="10 bps"
                  stroke="#ff7e84"
                  strokeWidth={2.5}
                  dot={false}
                  connectNulls
                />

              </LineChart>

            </ResponsiveContainer>

          </motion.div>


          <motion.div
            className="research-chart-card backtest-drawdown-card"
            initial={{
              opacity: 0,
              y: 20,
            }}
            whileInView={{
              opacity: 1,
              y: 0,
            }}
            viewport={{
              once: true,
            }}
          >

            <div className="chart-card-header">

              <div>

                <span className="eyebrow">
                  DRAWDOWN
                </span>

                <h3>
                  {selectedCost} bps drawdown path
                </h3>

              </div>

              <div className="chart-note">
                {TEST_NAMES[selectedTest]}
              </div>

            </div>


            <ResponsiveContainer
              width="100%"
              height={390}
            >

              <LineChart data={drawdownChart}>

                <CartesianGrid
                  strokeDasharray="4 4"
                  stroke="rgba(255,255,255,0.045)"
                  vertical={false}
                />

                <XAxis
                  dataKey="datetime"
                  minTickGap={45}
                  tickFormatter={formatBacktestDate}
                  tick={{
                    fill: "#737d96",
                    fontSize: 10,
                  }}
                  axisLine={false}
                  tickLine={false}
                />

                <YAxis
                  tickFormatter={(value) =>
                    `${Number(value).toFixed(0)}%`
                  }
                  tick={{
                    fill: "#59647d",
                    fontSize: 10,
                  }}
                  axisLine={false}
                  tickLine={false}
                />

                <Tooltip
                  labelFormatter={formatBacktestDate}
                  contentStyle={{
                    background: "#111827",
                    border:
                      "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "10px",
                  }}
                  formatter={(value) => [
                    `${Number(value).toFixed(2)}%`,
                    "Drawdown",
                  ]}
                />

                <ReferenceLine
                  y={0}
                  stroke="rgba(255,255,255,0.16)"
                />

                <Line
                  type="monotone"
                  dataKey="drawdownPct"
                  name="Drawdown"
                  stroke="#ff7e84"
                  strokeWidth={2.5}
                  dot={false}
                />

              </LineChart>

            </ResponsiveContainer>

          </motion.div>

        </div>


        {/* MAIN CHART */}



        <div className="execution-chart-grid">



          <motion.div

            className="research-chart-card execution-main-chart"

            initial={{

              opacity: 0,

              y: 20,

            }}

            whileInView={{

              opacity: 1,

              y: 0,

            }}

            viewport={{

              once: true,

            }}

          >



            <div className="chart-card-header">



              <div>



                <span className="eyebrow">

                  COST CURVE

                </span>



                <h3>

                  Return vs transaction cost

                </h3>



              </div>





              <div className="chart-note">

                One-way hypothetical cost

              </div>



            </div>





            <ResponsiveContainer

              width="100%"

              height={370}

            >



              <LineChart

                data={costChart}

              >



                <CartesianGrid

                  strokeDasharray="4 4"

                  stroke="rgba(255,255,255,0.045)"

                  vertical={false}

                />





                <XAxis

                  dataKey="cost"

                  tick={{

                    fill: "#737d96",

                    fontSize: 10,

                  }}

                  axisLine={false}

                  tickLine={false}

                  label={{

                    value:

                      "Transaction cost (bps)",

                    position:

                      "insideBottom",

                    offset: -5,

                    fill:

                      "#4f5971",

                    fontSize: 9,

                  }}

                />





                <YAxis

                  tick={{

                    fill: "#59647d",

                    fontSize: 10,

                  }}

                  axisLine={false}

                  tickLine={false}

                />





                <Tooltip

                  contentStyle={{

                    background:

                      "#111827",

                    border:

                      "1px solid rgba(255,255,255,0.08)",

                    borderRadius:

                      "10px",

                  }}

                  formatter={(

                    value

                  ) => [

                    `${Number(value).toFixed(2)}%`,

                    "Return",

                  ]}

                />





                <ReferenceLine

                  y={0}

                  stroke="rgba(255,255,255,0.18)"

                />





                <Line

                  type="monotone"

                  dataKey="Validation"

                  stroke="#8d79ff"

                  strokeWidth={3}

                  dot={{

                    r: 4,

                  }}

                  animationDuration={1200}

                />





                <Line

                  type="monotone"

                  dataKey="Time Holdout"

                  stroke="#63c7ff"

                  strokeWidth={3}

                  dot={{

                    r: 4,

                  }}

                  animationDuration={1400}

                />





                <Line

                  type="monotone"

                  dataKey="Asset Holdout"

                  stroke="#3ee2aa"

                  strokeWidth={3}

                  dot={{

                    r: 4,

                  }}

                  animationDuration={1600}

                />



              </LineChart>



            </ResponsiveContainer>



          </motion.div>





          {/* CURRENT COST BAR */}



          <motion.div

            className="research-chart-card"

            initial={{

              opacity: 0,

              y: 20,

            }}

            whileInView={{

              opacity: 1,

              y: 0,

            }}

            viewport={{

              once: true,

            }}

          >



            <div className="chart-card-header">



              <div>



                <span className="eyebrow">

                  SELECTED SCENARIO

                </span>



                <h3>

                  {selectedCost} bps performance

                </h3>



              </div>



            </div>





            <ResponsiveContainer

              width="100%"

              height={370}

            >



              <BarChart

                data={

                  currentResults

                }

              >



                <CartesianGrid

                  strokeDasharray="4 4"

                  stroke="rgba(255,255,255,0.045)"

                  vertical={false}

                />





                <XAxis

                  dataKey="displayName"

                  tick={{

                    fill: "#737d96",

                    fontSize: 10,

                  }}

                  axisLine={false}

                  tickLine={false}

                />





                <YAxis

                  tick={{

                    fill: "#59647d",

                    fontSize: 10,

                  }}

                  axisLine={false}

                  tickLine={false}

                />





                <Tooltip

                  contentStyle={{

                    background:

                      "#111827",

                    border:

                      "1px solid rgba(255,255,255,0.08)",

                    borderRadius:

                      "10px",

                  }}

                  formatter={(

                    value

                  ) => [

                    `${Number(value).toFixed(2)}%`,

                    "Return",

                  ]}

                />





                <ReferenceLine

                  y={0}

                  stroke="rgba(255,255,255,0.18)"

                />





                <Bar

                  dataKey="returnPct"

                  fill="#7762ff"

                  radius={[

                    7,

                    7,

                    0,

                    0,

                  ]}

                  animationDuration={900}

                />



              </BarChart>



            </ResponsiveContainer>



          </motion.div>



        </div>





        {/* AUTOPSY EXPLANATION */}



        <motion.div

          className="execution-autopsy-card"

          initial={{

            opacity: 0,

            y: 20,

          }}

          whileInView={{

            opacity: 1,

            y: 0,

          }}

          viewport={{

            once: true,

          }}

        >



          <div className="autopsy-left">



            <div className="autopsy-symbol">



              <Gauge

                size={29}

              />



            </div>



          </div>





          <div className="autopsy-copy">



            <span className="eyebrow">

              EXECUTION AUTOPSY

            </span>





            <h2>

              The signal survives.

              The implementation pays the price.

            </h2>





            <p>



              At zero assumed transaction cost,

              Validation, Final Time Holdout and

              Final Asset Holdout all remain

              profitable. As trading friction rises,

              the high-turnover hourly strategy loses

              much of its economic edge.



            </p>





            <div className="autopsy-comparison">



              <div>



                <span>

                  0 BPS

                </span>



                <strong>

                  Gross edge survives

                </strong>



              </div>





              <ArrowDownRight

                size={22}

              />





              <div className="cost-sensitive-box">



                <span>

                  2.5+ BPS

                </span>



                <strong>

                  Edge becomes fragile

                </strong>



              </div>



            </div>



          </div>



        </motion.div>



      </section>



    </motion.div>



  );



}





function RulePill({

  label,

  value,

}) {



  return (



    <div className="execution-rule-pill">



      <span>

        {label}

      </span>



      <strong>

        {value}

      </strong>



    </div>



  );



}





function ExecutionMetric({

  icon: Icon,

  label,

  value,

  detail,

  negative,

  delay,

}) {



  return (



    <motion.div

      className="execution-metric-card"

      initial={{

        opacity: 0,

        y: 18,

      }}

      animate={{

        opacity: 1,

        y: 0,

      }}

      transition={{

        delay,

      }}

      whileHover={{

        y: -5,

      }}

    >



      <div className="execution-metric-top">



        <div className="metric-icon">



          <Icon

            size={18}

          />



        </div>



        <span>

          {label}

        </span>



      </div>





      <strong

        className={

          negative

            ? "metric-negative"

            : "metric-positive"

        }

      >



        {value}



      </strong>





      <small>

        {detail}

      </small>



    </motion.div>



  );



}





export default Execution;