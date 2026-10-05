import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import {
  Activity,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  CircleDollarSign,
  FlaskConical,
  Gauge,
  ShieldCheck,
  TriangleAlert,
  Zap,
} from "lucide-react";


const stageNames = {
  Development: "Development",
  Validation: "Validation",
  FinalTimeHoldout: "Time Holdout",
  FinalAssetHoldout: "Asset Holdout",
};


const executionNames = {
  Validation6: "Validation",
  FinalTime20: "Time Holdout",
  FinalAsset3: "Asset Holdout",
};


function FactorAutopsy() {

  const [data, setData] =
    useState(null);


  useEffect(() => {

    fetch("/data/research.json")
      .then(
        (response) =>
          response.json()
      )
      .then(
        (result) =>
          setData(result)
      )
      .catch((error) => {

        console.error(
          "Failed to load autopsy data:",
          error
        );

      });

  }, []);


  const grossResults =
    useMemo(() => {

      if (!data) return [];

      return data.execution
        .filter(
          (item) =>
            item.costBps === 0
        )
        .map((item) => ({
          ...item,
          name:
            executionNames[
              item.test
            ] ?? item.test,
        }));

    }, [data]);


  const costResults =
    useMemo(() => {

      if (!data) return [];

      return data.execution
        .filter(
          (item) =>
            item.costBps === 2.5
        )
        .map((item) => ({
          ...item,
          name:
            executionNames[
              item.test
            ] ?? item.test,
        }));

    }, [data]);


  if (!data) {

    return (
      <div className="validation-loading">
        Loading factor autopsy...
      </div>
    );

  }


  return (

    <motion.div
      className="autopsy-page"
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

      {/* ========================================
          HERO
      ======================================== */}

      <section className="autopsy-hero">

        <div className="autopsy-hero-copy">

          <div className="hero-badge">

            <span className="badge-dot"></span>

            FINAL RESEARCH DIAGNOSIS

          </div>


          <h1>

            A signal can be
            <br />

            <span>
              real
            </span>

            {" "}and still be
            <br />

            difficult to trade.

          </h1>


          <p>

            rFactor Lab separates statistical
            predictability from economic
            implementation so promising factors are
            not judged only by attractive backtest
            returns.

          </p>

        </div>


        <motion.div
          className="autopsy-verdict-panel"
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

          <div className="verdict-row signal-verdict">

            <div className="verdict-icon success">

              <ShieldCheck
                size={25}
              />

            </div>


            <div>

              <span>
                SIGNAL
              </span>

              <strong>
                VALIDATED
              </strong>

              <small>
                Predictive relationship
                survived holdouts
              </small>

            </div>

          </div>


          <div className="verdict-divider">

            <div></div>

            <span>
              BUT
            </span>

            <div></div>

          </div>


          <div className="verdict-row execution-verdict">

            <div className="verdict-icon warning">

              <TriangleAlert
                size={25}
              />

            </div>


            <div>

              <span>
                EXECUTION
              </span>

              <strong>
                COST-SENSITIVE
              </strong>

              <small>
                Turnover consumes
                much of the edge
              </small>

            </div>

          </div>

        </motion.div>

      </section>


      {/* ========================================
          FINAL FACTOR
      ======================================== */}

      <section className="content-section autopsy-content">

        <div className="autopsy-factor-card">

          <div className="factor-symbol">

            <BrainCircuit
              size={30}
            />

          </div>


          <div className="factor-main-copy">

            <span className="eyebrow">
              FINAL FACTOR
            </span>


            <h2>
              1-hour cross-sectional reversal
            </h2>


            <p>

              Assets with stronger relative returns
              during the previous hour tended to rank
              weaker during the following hour, while
              recent relative losers tended to recover.

            </p>

          </div>


          <div className="factor-mechanics">

            <Mechanic
              label="SIGNAL"
              value="1H Momentum"
            />

            <ArrowRight
              size={18}
            />

            <Mechanic
              label="RELATION"
              value="Negative"
            />

            <ArrowRight
              size={18}
            />

            <Mechanic
              label="TARGET"
              value="Next 1H"
            />

          </div>

        </div>


        {/* ========================================
            RESEARCH TRAIL
        ======================================== */}

        <div className="autopsy-section-heading">

          <div>

            <span className="eyebrow">
              RESEARCH TRAIL
            </span>

            <h2>
              The signal survived every stage
            </h2>

          </div>


          <div className="survival-badge">

            <CheckCircle2
              size={15}
            />

            4 / 4 stages negative

          </div>

        </div>


        <div className="autopsy-timeline">

          {data.validation.map(
            (stage, index) => (

              <motion.div
                className="autopsy-stage"
                key={stage.stage}
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
                transition={{
                  delay:
                    index * 0.08,
                }}
              >

                <div className="stage-top">

                  <div className="stage-number">

                    {String(
                      index + 1
                    ).padStart(
                      2,
                      "0"
                    )}

                  </div>


                  <ShieldCheck
                    size={17}
                  />

                </div>


                <span className="stage-name">

                  {
                    stageNames[
                      stage.stage
                    ] ??
                    stage.stage
                  }

                </span>


                <strong className="stage-ic">

                  {stage.meanIC.toFixed(4)}

                </strong>


                <small>

                  Mean IC

                </small>


                <div className="stage-meta">

                  {stage.timestamps.toLocaleString()}
                  {" "}timestamps

                </div>


                {index <
                  data.validation.length -
                    1 && (

                  <div className="timeline-line">

                    <motion.div
                      initial={{
                        width: 0,
                      }}
                      whileInView={{
                        width:
                          "100%",
                      }}
                      viewport={{
                        once:
                          true,
                      }}
                      transition={{
                        delay:
                          0.2 +
                          index *
                            0.1,
                        duration:
                          0.6,
                      }}
                    />

                  </div>

                )}

              </motion.div>

            )
          )}

        </div>


        {/* ========================================
            GROSS VS COST
        ======================================== */}

        <div className="autopsy-section-heading economics-heading">

          <div>

            <span className="eyebrow">
              ECONOMIC AUTOPSY
            </span>

            <h2>
              Where does the edge disappear?
            </h2>

          </div>

        </div>


        <div className="economics-grid">

          {grossResults.map(
            (gross) => {

              const cost =
                costResults.find(
                  (item) =>
                    item.test ===
                    gross.test
                );


              return (

                <EconomicsCard
                  key={
                    gross.test
                  }
                  name={
                    gross.name
                  }
                  gross={
                    gross.returnPct
                  }
                  net={
                    cost?.returnPct ??
                    0
                  }
                  turnover={
                    cost?.turnover ??
                    gross.turnover
                  }
                />

              );

            }
          )}

        </div>


        {/* ========================================
            CAUSE ANALYSIS
        ======================================== */}

        <div className="diagnosis-grid">

          <DiagnosisCard
            icon={Zap}
            status="PASS"
            title="Predictive Structure"
            text={
              "Negative IC persisted through development, validation, future time and separate assets."
            }
            type="success"
            delay={0}
          />


          <DiagnosisCard
            icon={ShieldCheck}
            status="PASS"
            title="Out-of-Sample Stability"
            text={
              "The factor direction survived independently selected validation and holdout datasets."
            }
            type="success"
            delay={0.1}
          />


          <DiagnosisCard
            icon={Gauge}
            status="LIMITATION"
            title="Portfolio Turnover"
            text={
              "Even after capping hourly turnover near 0.50, frequent repositioning remains substantial."
            }
            type="warning"
            delay={0.2}
          />


          <DiagnosisCard
            icon={CircleDollarSign}
            status="LIMITATION"
            title="Transaction Costs"
            text={
              "A hypothetical 2.5 bps one-way cost materially reduces or eliminates returns in some tests."
            }
            type="warning"
            delay={0.3}
          />

        </div>


        {/* ========================================
            FINAL CONCLUSION
        ======================================== */}

        <motion.div
          className="final-diagnosis"
          initial={{
            opacity: 0,
            y: 25,
          }}
          whileInView={{
            opacity: 1,
            y: 0,
          }}
          viewport={{
            once: true,
          }}
        >

          <div className="final-diagnosis-icon">

            <FlaskConical
              size={32}
            />

          </div>


          <div className="final-diagnosis-copy">

            <span className="eyebrow">
              FINAL DIAGNOSIS
            </span>


            <h2>

              Validated factor.
              <br />

              <span>
                Cost-sensitive strategy.
              </span>

            </h2>


            <p>

              The short-term reversal relationship
              appears persistent across multiple
              independent tests. However, its current
              hourly long-short implementation requires
              enough turnover that transaction costs can
              overwhelm the statistical edge.

            </p>


            <div className="diagnosis-tags">

              <span className="tag-pass">
                ✓ Signal validated
              </span>

              <span className="tag-pass">
                ✓ Holdouts passed
              </span>

              <span className="tag-warning">
                ⚠ High turnover
              </span>

              <span className="tag-warning">
                ⚠ Cost sensitivity
              </span>

            </div>

          </div>


          <div className="diagnosis-score">

            <span>
              RESEARCH STATUS
            </span>

            <strong>
              COMPLETE
            </strong>

            <div className="complete-line">

              <motion.div
                initial={{
                  width: 0,
                }}
                whileInView={{
                  width:
                    "100%",
                }}
                viewport={{
                  once: true,
                }}
                transition={{
                  duration: 1.3,
                }}
              />

            </div>

          </div>

        </motion.div>

      </section>

    </motion.div>

  );

}


function Mechanic({
  label,
  value,
}) {

  return (

    <div className="mechanic">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>

  );

}


function EconomicsCard({
  name,
  gross,
  net,
  turnover,
}) {

  const loss =
    gross - net;


  return (

    <motion.div
      className="economics-card"
      whileHover={{
        y: -5,
      }}
    >

      <div className="economics-title">

        <Activity
          size={17}
        />

        <span>
          {name}
        </span>

      </div>


      <div className="return-comparison">

        <div>

          <span>
            0 BPS
          </span>

          <strong className="gross-value">

            +{gross.toFixed(2)}%

          </strong>

        </div>


        <ArrowRight
          size={18}
        />


        <div>

          <span>
            2.5 BPS
          </span>

          <strong
            className={
              net >= 0
                ? "net-positive"
                : "net-negative"
            }
          >

            {net >= 0
              ? "+"
              : ""}
            {net.toFixed(2)}%

          </strong>

        </div>

      </div>


      <div className="edge-loss-bar">

        <div
          style={{
            width:
              `${Math.min(
                100,
                Math.max(
                  5,
                  Math.abs(
                    loss
                  ) *
                    3
                )
              )}%`,
          }}
        ></div>

      </div>


      <div className="economics-footer">

        <span>
          Edge lost to friction
        </span>

        <strong>
          {loss.toFixed(2)} pts
        </strong>

      </div>


      <div className="economics-turnover">

        Avg turnover:
        {" "}
        {turnover.toFixed(2)}

      </div>

    </motion.div>

  );

}


function DiagnosisCard({
  icon: Icon,
  status,
  title,
  text,
  type,
  delay,
}) {

  return (

    <motion.div
      className={`diagnosis-card ${type}`}
      initial={{
        opacity: 0,
        y: 18,
      }}
      whileInView={{
        opacity: 1,
        y: 0,
      }}
      viewport={{
        once: true,
      }}
      transition={{
        delay,
      }}
      whileHover={{
        y: -5,
      }}
    >

      <div className="diagnosis-card-top">

        <div className="diagnosis-small-icon">

          <Icon
            size={19}
          />

        </div>


        <span>
          {status}
        </span>

      </div>


      <h3>
        {title}
      </h3>


      <p>
        {text}
      </p>

    </motion.div>

  );

}


export default FactorAutopsy;