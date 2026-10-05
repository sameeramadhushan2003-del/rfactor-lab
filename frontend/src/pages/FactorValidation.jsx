import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  ReferenceLine,
} from "recharts";

import {
  ShieldCheck,
  Database,
  Activity,
  TrendingDown,
  CheckCircle2,
} from "lucide-react";


function FactorValidation() {

  const [data, setData] = useState(null);


  useEffect(() => {

    fetch("/data/research.json")
      .then((response) => response.json())
      .then((result) => {

        setData(result);

      })
      .catch((error) => {

        console.error(
          "Failed to load research data:",
          error
        );

      });

  }, []);


  if (!data) {

    return (
      <div className="validation-loading">
        Loading research data...
      </div>
    );

  }


  const validation =
    data.validation;


  const folds =
    data.folds;


  return (

    <motion.div
      className="validation-page"
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

      <section className="page-header">

        <div>

          <div className="hero-badge">

            <span className="badge-dot"></span>

            INDEPENDENT FACTOR VALIDATION

          </div>


          <h1>

            Evidence over
            <br />

            <span>
              intuition.
            </span>

          </h1>


          <p>

            The final factor was frozen before
            validation and tested across different
            assets, future time periods and a final
            independent asset holdout.

          </p>

        </div>


        <motion.div
          className="validation-status-card"
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

          <ShieldCheck
            size={33}
          />

          <span>
            FACTOR STATUS
          </span>

          <h2>
            VALIDATED
          </h2>

          <p>
            Negative IC survived every
            research stage.
          </p>

          <div className="status-success">

            <CheckCircle2
              size={16}
            />

            Passed holdout testing

          </div>

        </motion.div>

      </section>


      {/* METRICS */}

      <section className="content-section validation-content">

        <div className="validation-metrics">

          <MetricCard
            icon={Database}
            label="Development"
            value="-0.0744"
            detail="3,762 timestamps"
            delay={0}
          />


          <MetricCard
            icon={ShieldCheck}
            label="Validation"
            value="-0.0351"
            detail="893 timestamps"
            delay={0.1}
          />


          <MetricCard
            icon={Activity}
            label="Time Holdout"
            value="-0.0708"
            detail="1,066 timestamps"
            delay={0.2}
          />


          <MetricCard
            icon={TrendingDown}
            label="Asset Holdout"
            value="-0.0812"
            detail="AMD · GLW · META"
            delay={0.3}
          />

        </div>


        {/* IC CHART */}

        <div className="chart-grid">

          <motion.div
            className="research-chart-card chart-large"
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
                  OUT-OF-SAMPLE TESTING
                </span>

                <h3>
                  Mean IC across stages
                </h3>

              </div>


              <div className="validated-pill">

                <ShieldCheck
                  size={14}
                />

                Consistent direction

              </div>

            </div>


            <div className="chart-wrapper">

              <ResponsiveContainer
                width="100%"
                height={340}
              >

                <BarChart
                  data={validation}
                >

                  <CartesianGrid
                    strokeDasharray="4 4"
                    stroke="rgba(255,255,255,0.045)"
                    vertical={false}
                  />


                  <XAxis
                    dataKey="stage"
                    tick={{
                      fill: "#737d96",
                      fontSize: 11,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />


                  <YAxis
                    domain={[
                      -0.1,
                      0.02,
                    ]}
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
                      color:
                        "#fff",
                    }}
                  />


                  <ReferenceLine
                    y={0}
                    stroke="rgba(255,255,255,0.16)"
                  />


                  <Bar
                    dataKey="meanIC"
                    fill="#7864ff"
                    radius={[
                      7,
                      7,
                      0,
                      0,
                    ]}
                    animationDuration={1200}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          </motion.div>


          {/* FOLDS */}

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
                  WALK-FORWARD
                </span>

                <h3>
                  Development stability
                </h3>

              </div>

            </div>


            <div className="chart-wrapper">

              <ResponsiveContainer
                width="100%"
                height={340}
              >

                <LineChart
                  data={folds}
                >

                  <CartesianGrid
                    strokeDasharray="4 4"
                    stroke="rgba(255,255,255,0.045)"
                    vertical={false}
                  />


                  <XAxis
                    dataKey="name"
                    tick={{
                      fill: "#737d96",
                      fontSize: 11,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />


                  <YAxis
                    domain={[
                      -0.1,
                      0,
                    ]}
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
                  />


                  <Line
                    type="monotone"
                    dataKey="ic"
                    stroke="#6ec8ff"
                    strokeWidth={3}
                    dot={{
                      fill: "#8a75ff",
                      strokeWidth: 0,
                      r: 5,
                    }}
                    activeDot={{
                      r: 7,
                    }}
                    animationDuration={1500}
                  />

                </LineChart>

              </ResponsiveContainer>

            </div>

          </motion.div>

        </div>


        {/* INTERPRETATION */}

        <motion.div
          className="validation-conclusion"
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

          <div className="conclusion-icon">

            <ShieldCheck
              size={28}
            />

          </div>


          <div>

            <span className="eyebrow">
              VALIDATION CONCLUSION
            </span>


            <h2>

              The reversal relationship
              survived outside the
              development sample.

            </h2>


            <p>

              Mean IC remained negative during
              Development, Validation, the future-time
              holdout and the completely separate
              AMD / GLW / META asset holdout.

            </p>


            <div className="evidence-tags">

              <span>
                ✓ Different assets
              </span>

              <span>
                ✓ Future time
              </span>

              <span>
                ✓ Four walk-forward folds
              </span>

              <span>
                ✓ Independent holdout
              </span>

            </div>

          </div>

        </motion.div>

      </section>

    </motion.div>

  );

}


function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
  delay,
}) {

  return (

    <motion.div
      className="validation-metric-card"
      initial={{
        opacity: 0,
        y: 20,
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

      <div className="metric-icon">

        <Icon
          size={18}
        />

      </div>


      <span>
        {label}
      </span>


      <strong>
        {value}
      </strong>


      <small>
        {detail}
      </small>

    </motion.div>

  );

}


export default FactorValidation;