import { motion } from "framer-motion";

import {
  Activity,
  CheckCircle2,
  Database,
  Filter,
  FlaskConical,
  LockKeyhole,
  Microscope,
  ShieldCheck,
  TimerReset,
  TriangleAlert,
} from "lucide-react";


const researchSteps = [
  {
    number: "01",
    title: "Universe Discovery",
    subtitle: "Bitget Reality universe",
    icon: Database,
    status: "COMPLETE",
    type: "normal",
    metric: "2,587 pairs",
    description:
      "Started from the complete Bitget Reality stock universe rather than selecting only familiar assets.",
    detail:
      "This reduced selection bias at the beginning of the research process.",
  },

  {
    number: "02",
    title: "Tradability Filter",
    subtitle: "Weekend-capable universe",
    icon: Filter,
    status: "COMPLETE",
    type: "normal",
    metric: "90 assets",
    description:
      "Filtered the Reality universe to assets identified as weekend-tradable for the initial research stage.",
    detail:
      "The universe was narrowed using product availability rather than factor performance.",
  },

  {
    number: "03",
    title: "Long-History Filter",
    subtitle: "Historical research universe",
    icon: TimerReset,
    status: "COMPLETE",
    type: "normal",
    metric: "24 assets",
    description:
      "Selected assets with at least approximately 365 days of historical candle coverage.",
    detail:
      "Twenty-four assets provided sufficient history for the V2 research cycle.",
  },

  {
    number: "04",
    title: "Data Quality",
    subtitle: "Market availability mask",
    icon: ShieldCheck,
    status: "PASSED",
    type: "success",
    metric: "23 approved",
    description:
      "A market-availability mask was used to distinguish genuine missing data from hours where the wider universe was unavailable.",
    detail:
      "Twenty-three of the twenty-four long-history assets passed the corrected quality criteria.",
  },

  {
    number: "05",
    title: "Research Split",
    subtitle: "Independent asset groups",
    icon: FlaskConical,
    status: "FROZEN",
    type: "locked",
    metric: "14 / 6 / 3",
    description:
      "The eligible universe was separated into Development, Validation and Asset Holdout groups before final factor evaluation.",
    detail:
      "14 Development assets, 6 Validation assets and 3 final Asset Holdout assets.",
  },

  {
    number: "06",
    title: "Factor Discovery",
    subtitle: "Development data only",
    icon: Microscope,
    status: "DISCOVERED",
    type: "success",
    metric: "1H Reversal",
    description:
      "Multiple predefined price-based factors and forward-return horizons were tested using only the Development sample.",
    detail:
      "The strongest stable candidate was 1-hour cross-sectional momentum predicting next-hour returns with an expected negative IC.",
  },

  {
    number: "07",
    title: "Factor Frozen",
    subtitle: "No more factor tuning",
    icon: LockKeyhole,
    status: "LOCKED",
    type: "locked",
    metric: "Before validation",
    description:
      "The 1-hour reversal factor, target horizon and expected direction were frozen before inspecting independent Validation results.",
    detail:
      "This prevents changing the signal after observing out-of-sample performance.",
  },

  {
    number: "08",
    title: "Independent Validation",
    subtitle: "Validation assets + future period",
    icon: ShieldCheck,
    status: "PASSED",
    type: "success",
    metric: "IC -0.0351",
    description:
      "The frozen factor retained the expected negative relationship on the independently separated Validation sample.",
    detail:
      "Both validation halves remained negative, supporting the reversal hypothesis.",
  },

  {
    number: "09",
    title: "Final Time Holdout",
    subtitle: "Future unseen period",
    icon: CheckCircle2,
    status: "PASSED",
    type: "success",
    metric: "IC -0.0708",
    description:
      "The frozen factor was evaluated on the final future-time period using the broader research universe.",
    detail:
      "The final time holdout contained 1,066 IC timestamps and preserved the expected negative relationship.",
  },

  {
    number: "10",
    title: "Final Asset Holdout",
    subtitle: "AMD · GLW · META",
    icon: CheckCircle2,
    status: "PASSED",
    type: "success",
    metric: "IC -0.0812",
    description:
      "The factor was also tested on three separately held-out assets during the final time period.",
    detail:
      "This provided an additional asset-level generalization check, although the three-asset IC is naturally coarse.",
  },

  {
    number: "11",
    title: "Execution Study",
    subtitle: "Economic implementation",
    icon: Activity,
    status: "TESTED",
    type: "warning",
    metric: "0–10 bps",
    description:
      "After statistical validation, the factor was translated into long-short portfolio rules and tested under hypothetical transaction-cost assumptions.",
    detail:
      "A turnover cap reduced trading activity, but the implementation remained highly sensitive to costs.",
  },

  {
    number: "12",
    title: "Factor Autopsy",
    subtitle: "Final research diagnosis",
    icon: TriangleAlert,
    status: "COMPLETE",
    type: "warning",
    metric: "Cost-sensitive",
    description:
      "The final stage separated statistical factor quality from economic trading performance.",
    detail:
      "Final conclusion: validated historical factor evidence, but a cost-sensitive current implementation.",
  },
];


function ResearchTimeline() {
  return (
    <motion.div
      className="timeline-page"
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

      <section className="timeline-hero">

        <div className="timeline-hero-copy">

          <div className="hero-badge">
            <LockKeyhole size={12} />

            RESEARCH DISCIPLINE
          </div>


          <h1>
            From universe
            <br />

            <span>
              to evidence.
            </span>
          </h1>


          <p>
            Follow the complete rFactor Lab research
            process from universe construction to final
            factor autopsy. The sequence highlights where
            information was frozen before independent
            validation.
          </p>

        </div>


        <motion.div
          className="timeline-principle-card"
          initial={{
            opacity: 0,
            scale: 0.95,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
          transition={{
            delay: 0.15,
          }}
        >
          <LockKeyhole size={30} />

          <span>
            CORE PRINCIPLE
          </span>

          <h2>
            Freeze before validation.
          </h2>

          <p>
            Factor selection was completed on Development
            data before independent Validation and final
            Holdout tests were inspected.
          </p>

          <div className="principle-status">
            <CheckCircle2 size={15} />

            Research split preserved
          </div>

        </motion.div>

      </section>


      {/* SUMMARY */}

      <section className="content-section timeline-content">

        <div className="timeline-summary-grid">

          <SummaryCard
            label="INITIAL UNIVERSE"
            value="2,587"
            description="Reality pairs"
          />

          <SummaryCard
            label="QUALITY UNIVERSE"
            value="23"
            description="Approved assets"
          />

          <SummaryCard
            label="DEVELOPMENT"
            value="14"
            description="Factor discovery assets"
          />

          <SummaryCard
            label="VALIDATION"
            value="6"
            description="Independent assets"
          />

          <SummaryCard
            label="FINAL HOLDOUT"
            value="3"
            description="Separate assets"
          />

        </div>


        {/* TIMELINE HEADING */}

        <div className="timeline-section-heading">

          <div>
            <span className="eyebrow">
              METHODOLOGY TRACKER
            </span>

            <h2>
              Research journey
            </h2>
          </div>


          <div className="timeline-complete-badge">
            <CheckCircle2 size={15} />

            12 stages complete
          </div>

        </div>


        {/* TIMELINE */}

        <div className="research-timeline">

          {researchSteps.map(
            (step, index) => {

              const Icon = step.icon;

              return (
                <motion.div
                  key={step.number}
                  className={`timeline-step ${step.type}`}
                  initial={{
                    opacity: 0,
                    y: 24,
                  }}
                  whileInView={{
                    opacity: 1,
                    y: 0,
                  }}
                  viewport={{
                    once: true,
                    amount: 0.15,
                  }}
                  transition={{
                    delay:
                      Math.min(
                        index * 0.04,
                        0.3
                      ),
                  }}
                >

                  {/* LINE */}

                  {index !==
                    researchSteps.length - 1 && (
                    <div className="timeline-vertical-line">
                      <motion.div
                        initial={{
                          height: 0,
                        }}
                        whileInView={{
                          height: "100%",
                        }}
                        viewport={{
                          once: true,
                        }}
                        transition={{
                          duration: 0.7,
                        }}
                      />
                    </div>
                  )}


                  {/* NUMBER / ICON */}

                  <div className="timeline-marker">

                    <Icon size={20} />

                  </div>


                  {/* BODY */}

                  <div className="timeline-step-card">

                    <div className="timeline-card-top">

                      <div>
                        <span className="timeline-number">
                          STEP {step.number}
                        </span>

                        <h3>
                          {step.title}
                        </h3>

                        <small>
                          {step.subtitle}
                        </small>
                      </div>


                      <div
                        className={`timeline-status ${step.type}`}
                      >
                        {step.status}
                      </div>

                    </div>


                    <div className="timeline-card-body">

                      <div className="timeline-text">

                        <p>
                          {step.description}
                        </p>

                        <span>
                          {step.detail}
                        </span>

                      </div>


                      <div className="timeline-metric">

                        <span>
                          KEY RESULT
                        </span>

                        <strong>
                          {step.metric}
                        </strong>

                      </div>

                    </div>

                  </div>

                </motion.div>
              );

            }
          )}

        </div>


        {/* FINAL DISCIPLINE CARD */}

        <motion.div
          className="research-discipline-card"
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

          <div className="discipline-icon">
            <ShieldCheck size={30} />
          </div>


          <div>

            <span className="eyebrow">
              WHY THIS MATTERS
            </span>

            <h2>
              Strong backtests are not enough.
            </h2>

            <p>
              rFactor Lab separates factor discovery,
              independent validation, final holdouts and
              execution analysis. This makes it possible
              to identify when a statistically interesting
              signal does not automatically translate into
              a robust trading implementation.
            </p>

          </div>


          <div className="discipline-verdict">

            <div>
              <span>
                FACTOR
              </span>

              <strong className="discipline-success">
                VALIDATED
              </strong>
            </div>


            <div>
              <span>
                EXECUTION
              </span>

              <strong className="discipline-warning">
                COST-SENSITIVE
              </strong>
            </div>

          </div>

        </motion.div>

      </section>

    </motion.div>
  );
}


function SummaryCard({
  label,
  value,
  description,
}) {
  return (
    <motion.div
      className="timeline-summary-card"
      whileHover={{
        y: -4,
      }}
    >
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {description}
      </small>
    </motion.div>
  );
}


export default ResearchTimeline;