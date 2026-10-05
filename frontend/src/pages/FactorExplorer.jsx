import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import {
  Activity,
  BarChart3,
  CheckCircle2,
  FlaskConical,
  Gauge,
  Search,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


function prettyFactor(name) {

  const names = {
    momentum_1h: "1H Momentum",
    momentum_3h: "3H Momentum",
    momentum_6h: "6H Momentum",
    momentum_24h: "24H Momentum",

    vol_norm_momentum_6h:
      "Vol-Normalized 6H Momentum",

    volatility_expansion:
      "Volatility Expansion",

    distance_ma24:
      "Distance from MA24",

    distance_ma72:
      "Distance from MA72",
  };

  return names[name] ?? name;
}


function prettyTarget(name) {

  const names = {
    forward_return_1h: "Next 1 Hour",
    forward_return_3h: "Next 3 Hours",
    forward_return_6h: "Next 6 Hours",
  };

  return names[name] ?? name;
}


function FactorExplorer() {

  const [data, setData] = useState(null);

  const [selectedFactor, setSelectedFactor] =
    useState("momentum_1h");

  const [selectedTarget, setSelectedTarget] =
    useState("forward_return_1h");

  const [search, setSearch] = useState("");


  useEffect(() => {

    fetch("/data/factors.json")
      .then((response) => response.json())
      .then((result) => {

        setData(result);

        const preferred =
          result.candidates.find(
            (item) =>
              item.factor === "momentum_1h" &&
              item.target === "forward_return_1h"
          );

        if (!preferred && result.candidates.length) {

          setSelectedFactor(
            result.candidates[0].factor
          );

          setSelectedTarget(
            result.candidates[0].target
          );

        }

      })
      .catch((error) => {

        console.error(
          "Could not load factor data:",
          error
        );

      });

  }, []);


  const selected = useMemo(() => {

    if (!data) return null;

    return data.candidates.find(
      (item) =>
        item.factor === selectedFactor &&
        item.target === selectedTarget
    );

  }, [
    data,
    selectedFactor,
    selectedTarget,
  ]);


  const availableTargets = useMemo(() => {

    if (!data) return [];

    return data.candidates
      .filter(
        (item) =>
          item.factor === selectedFactor
      )
      .map(
        (item) => item.target
      );

  }, [
    data,
    selectedFactor,
  ]);


  const foldData = useMemo(() => {

    if (!selected) return [];

    return selected.folds.map(
      (value, index) => ({
        name: `Fold ${index + 1}`,
        ic: value,
      })
    );

  }, [selected]);


  const comparisonData = useMemo(() => {

    if (!data) return [];

    return [...data.candidates]
      .filter((item) =>
        `${item.factor} ${item.target}`
          .toLowerCase()
          .includes(
            search.toLowerCase()
          )
      )
      .sort(
        (a, b) =>
          Math.abs(b.meanIC) -
          Math.abs(a.meanIC)
      );

  }, [data, search]);


  function chooseFactor(item) {

    setSelectedFactor(
      item.factor
    );

    setSelectedTarget(
      item.target
    );

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });

  }


  if (!data || !selected) {

    return (
      <div className="validation-loading">
        Loading Factor Explorer...
      </div>
    );

  }


  const direction =
    selected.meanIC < 0
      ? "Reversal"
      : "Momentum";


  return (

    <motion.div
      className="factor-explorer-page"
      initial={{
        opacity: 0,
        y: 18,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        duration: 0.45,
      }}
    >

      {/* HERO */}

      <section className="explorer-hero">

        <div>

          <div className="hero-badge">

            <FlaskConical size={12} />

            INTERACTIVE FACTOR LAB

          </div>


          <h1>

            Explore every
            <br />

            <span>
              candidate factor.
            </span>

          </h1>


          <p>

            Compare the actual Development-period
            factor tests used by rFactor Lab before
            the final signal was frozen.

          </p>

        </div>


        <div className="explorer-summary">

          <BarChart3 size={28} />

          <span>
            RESEARCH LIBRARY
          </span>

          <strong>
            {data.totalCandidates}
          </strong>

          <small>
            factor-target combinations tested
          </small>

        </div>

      </section>


      <section className="content-section explorer-content">

        {/* SELECTORS */}

        <div className="explorer-controls">

          <div className="control-group">

            <label>
              FACTOR
            </label>

            <select
              value={selectedFactor}
              onChange={(event) => {

                const factor =
                  event.target.value;

                setSelectedFactor(
                  factor
                );

                const first =
                  data.candidates.find(
                    (item) =>
                      item.factor === factor
                  );

                if (first) {

                  setSelectedTarget(
                    first.target
                  );

                }

              }}
            >

              {data.factors.map(
                (factor) => (

                  <option
                    key={factor}
                    value={factor}
                  >
                    {prettyFactor(factor)}
                  </option>

                )
              )}

            </select>

          </div>


          <div className="control-group">

            <label>
              TARGET HORIZON
            </label>

            <select
              value={selectedTarget}
              onChange={(event) =>
                setSelectedTarget(
                  event.target.value
                )
              }
            >

              {availableTargets.map(
                (target) => (

                  <option
                    key={target}
                    value={target}
                  >
                    {prettyTarget(target)}
                  </option>

                )
              )}

            </select>

          </div>


          <div className="selected-status">

            {selected.passesStability ? (

              <>
                <CheckCircle2
                  size={18}
                />

                <div>

                  <span>
                    STABILITY
                  </span>

                  <strong>
                    PASSED
                  </strong>

                </div>
              </>

            ) : (

              <>
                <TriangleAlert
                  size={18}
                />

                <div>

                  <span>
                    STABILITY
                  </span>

                  <strong>
                    NOT PASSED
                  </strong>

                </div>
              </>

            )}

          </div>

        </div>


        {/* METRICS */}

        <div className="explorer-metrics">

          <Metric
            icon={Activity}
            label="MEAN IC"
            value={
              selected.meanIC.toFixed(4)
            }
          />

          <Metric
            icon={BarChart3}
            label="MEDIAN IC"
            value={
              selected.medianIC.toFixed(4)
            }
          />

          <Metric
            icon={Gauge}
            label="TIMESTAMPS"
            value={
              selected.timestamps
                .toLocaleString()
            }
          />

          <Metric
            icon={ShieldCheck}
            label="SIGNAL TYPE"
            value={direction}
          />

          <Metric
            icon={Activity}
            label="NAIVE T-STAT"
            value={
              selected.naiveTStat.toFixed(2)
            }
          />

          <Metric
            icon={Gauge}
            label="POSITIVE IC"
            value={
              `${selected.positiveICPct.toFixed(1)}%`
            }
          />

        </div>


        {/* CHART */}

        <div className="explorer-chart-grid">

          <div className="explorer-chart-card">

            <div className="explorer-card-heading">

              <div>

                <span className="eyebrow">
                  WALK-FORWARD STABILITY
                </span>

                <h2>
                  Development folds
                </h2>

              </div>


              <div
                className={
                  selected.passesStability
                    ? "explorer-pass"
                    : "explorer-fail"
                }
              >

                {selected.passesStability
                  ? "STABLE"
                  : "UNSTABLE"}

              </div>

            </div>


            <div className="factor-chart">

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <BarChart
                  data={foldData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="rgba(255,255,255,0.06)"
                  />

                  <XAxis
                    dataKey="name"
                    tick={{
                      fill: "#65718b",
                      fontSize: 10,
                    }}
                    axisLine={false}
                    tickLine={false}
                  />

                  <YAxis
                    tick={{
                      fill: "#65718b",
                      fontSize: 10,
                    }}
                    axisLine={false}
                    tickLine={false}
                    width={48}
                  />

                  <Tooltip
                    contentStyle={{
                      background:
                        "#11182a",
                      border:
                        "1px solid rgba(255,255,255,0.08)",
                      borderRadius:
                        "10px",
                    }}
                    formatter={(value) => [
                      Number(value).toFixed(4),
                      "IC",
                    ]}
                  />

                  <Bar
                    dataKey="ic"
                    radius={[5, 5, 0, 0]}
                  >

                    {foldData.map(
                      (entry, index) => (

                        <Cell
                          key={index}
                          fill={
                            entry.ic < 0
                              ? "#7a67ff"
                              : "#55c6f6"
                          }
                        />

                      )
                    )}

                  </Bar>

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>


          {/* INTERPRETATION */}

          <div className="explorer-insight-card">

            <span className="eyebrow">
              FACTOR INTERPRETATION
            </span>


            <h2>
              {prettyFactor(
                selected.factor
              )}
            </h2>


            <div className="insight-row">

              <span>
                Target
              </span>

              <strong>
                {prettyTarget(
                  selected.target
                )}
              </strong>

            </div>


            <div className="insight-row">

              <span>
                Direction
              </span>

              <strong>
                {direction}
              </strong>

            </div>


            <div className="insight-row">

              <span>
                Mean IC
              </span>

              <strong>
                {selected.meanIC.toFixed(4)}
              </strong>

            </div>


            <div className="insight-row">

              <span>
                IC dispersion
              </span>

              <strong>
                {selected.stdIC.toFixed(4)}
              </strong>

            </div>


            <div className="factor-explanation">

              {selected.meanIC < 0
                ? (
                  <>
                    A negative IC means
                    relatively stronger recent
                    performers tended to rank
                    weaker in the future target
                    window.
                  </>
                )
                : (
                  <>
                    A positive IC means
                    relatively stronger recent
                    performers tended to retain
                    stronger future rankings.
                  </>
                )}

            </div>

          </div>

        </div>


        {/* ALL CANDIDATES */}

        <div className="candidate-section">

          <div className="candidate-header">

            <div>

              <span className="eyebrow">
                FACTOR LIBRARY
              </span>

              <h2>
                Compare all candidates
              </h2>

            </div>


            <div className="candidate-search">

              <Search size={15} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
                placeholder="Search factors..."
              />

            </div>

          </div>


          <div className="candidate-table">

            <div className="candidate-table-head">

              <span>
                FACTOR
              </span>

              <span>
                TARGET
              </span>

              <span>
                MEAN IC
              </span>

              <span>
                T-STAT
              </span>

              <span>
                FOLDS
              </span>

              <span>
                STATUS
              </span>

            </div>


            {comparisonData.map(
              (item) => (

                <button
                  key={
                    `${item.factor}-${item.target}`
                  }
                  className={
                    item.factor === selectedFactor &&
                    item.target === selectedTarget
                      ? "candidate-row selected"
                      : "candidate-row"
                  }
                  onClick={() =>
                    chooseFactor(item)
                  }
                >

                  <span>
                    {prettyFactor(
                      item.factor
                    )}
                  </span>

                  <span>
                    {prettyTarget(
                      item.target
                    )}
                  </span>

                  <strong>
                    {item.meanIC.toFixed(4)}
                  </strong>

                  <span>
                    {item.naiveTStat.toFixed(2)}
                  </span>

                  <span>
                    {
                      item.folds.filter(
                        (fold) =>
                          Math.sign(fold) ===
                          Math.sign(
                            item.meanIC
                          )
                      ).length
                    }
                    /4
                  </span>

                  <span
                    className={
                      item.passesStability
                        ? "table-pass"
                        : "table-fail"
                    }
                  >

                    {item.passesStability
                      ? "PASS"
                      : "FAIL"}

                  </span>

                </button>

              )
            )}

          </div>

        </div>

      </section>

    </motion.div>

  );

}


function Metric({
  icon: Icon,
  label,
  value,
}) {

  return (

    <motion.div
      className="explorer-metric"
      whileHover={{
        y: -4,
      }}
    >

      <div className="explorer-metric-icon">

        <Icon size={17} />

      </div>


      <div>

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

      </div>

    </motion.div>

  );

}


export default FactorExplorer;