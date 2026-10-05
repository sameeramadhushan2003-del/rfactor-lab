import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import {
  CheckCircle2,
  Download,
  FileText,
  Printer,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";


function ResearchReport() {
  const [research, setResearch] = useState(null);
  const [tokens, setTokens] = useState(null);
  const [factors, setFactors] = useState(null);


  useEffect(() => {
    Promise.all([
      fetch("/data/research.json").then((r) => r.json()),
      fetch("/data/tokens.json").then((r) => r.json()),
      fetch("/data/factors.json").then((r) => r.json()),
    ])
      .then(([researchData, tokenData, factorData]) => {
        setResearch(researchData);
        setTokens(tokenData);
        setFactors(factorData);
      })
      .catch((error) => {
        console.error(
          "Could not load report data:",
          error
        );
      });
  }, []);


  const results = useMemo(() => {
    if (!research) {
      return null;
    }

    const findStage = (name) =>
      research.validation.find(
        (item) =>
          item.stage === name
      );

    const findExecution = (
      test,
      cost
    ) =>
      research.execution.find(
        (item) =>
          item.test === test &&
          Number(item.costBps) ===
            Number(cost)
      );


    return {
      development:
        findStage("Development"),

      validation:
        findStage("Validation"),

      timeHoldout:
        findStage("FinalTimeHoldout"),

      assetHoldout:
        findStage("FinalAssetHoldout"),

      validationGross:
        findExecution(
          "Validation6",
          0
        ),

      validationCost:
        findExecution(
          "Validation6",
          2.5
        ),

      timeGross:
        findExecution(
          "FinalTime20",
          0
        ),

      timeCost:
        findExecution(
          "FinalTime20",
          2.5
        ),

      assetGross:
        findExecution(
          "FinalAsset3",
          0
        ),

      assetCost:
        findExecution(
          "FinalAsset3",
          2.5
        ),
    };
  }, [research]);


  function printReport() {
    window.print();
  }


  function downloadSummary() {
    if (
      !research ||
      !tokens ||
      !factors
    ) {
      return;
    }

    const output = {
      project:
        "rFactor Lab",

      generatedAt:
        new Date().toISOString(),

      research,
      tokenUniverse: {
        totalTokens:
          tokens.totalTokens,
      },

      factorLibrary: {
        totalCandidates:
          factors.totalCandidates,
      },

      conclusion:
        "Validated historical factor evidence with a cost-sensitive current implementation.",
    };


    const blob =
      new Blob(
        [
          JSON.stringify(
            output,
            null,
            2
          ),
        ],
        {
          type:
            "application/json",
        }
      );


    const url =
      URL.createObjectURL(
        blob
      );


    const link =
      document.createElement(
        "a"
      );

    link.href = url;

    link.download =
      "rFactor-Lab-Research-Summary.json";

    document.body.appendChild(
      link
    );

    link.click();

    link.remove();

    URL.revokeObjectURL(url);
  }


  if (
    !research ||
    !tokens ||
    !factors ||
    !results
  ) {
    return (
      <div className="validation-loading">
        Generating research report...
      </div>
    );
  }


  return (
    <motion.div
      className="report-page"
      initial={{
        opacity: 0,
        y: 18,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
    >

      {/* TOP ACTIONS */}

      <div className="report-actions">

        <div>
          <span className="eyebrow">
            RESEARCH EXPORT
          </span>

          <h2>
            Generated Research Report
          </h2>
        </div>


        <div className="report-action-buttons">

          <button
            className="secondary-button"
            onClick={
              downloadSummary
            }
          >
            <Download size={16} />

            Download JSON
          </button>


          <button
            className="primary-button"
            onClick={
              printReport
            }
          >
            <Printer size={16} />

            Print / Save PDF
          </button>

        </div>

      </div>


      {/* PRINTABLE REPORT */}

      <article
        className="research-report"
      >

        {/* COVER */}

        <section className="report-cover">

          <div className="report-logo">

            <FileText size={28} />

          </div>


          <span className="report-kicker">
            BITGET REALITY FACTOR RESEARCH
          </span>


          <h1>
            rFactor Lab
          </h1>


          <h2>
            Quantitative Factor Research Report
          </h2>


          <p>
            Systematic discovery, independent
            validation and economic evaluation of
            predictive factors across Bitget Reality
            rTokens.
          </p>


          <div className="report-cover-verdict">

            <div>
              <span>
                FACTOR STATUS
              </span>

              <strong className="report-success">
                VALIDATED
              </strong>
            </div>


            <div>
              <span>
                EXECUTION STATUS
              </span>

              <strong className="report-warning">
                COST-SENSITIVE
              </strong>
            </div>

          </div>

        </section>


        {/* EXECUTIVE SUMMARY */}

        <ReportSection
          number="01"
          title="Executive Summary"
        >

          <p>
            rFactor Lab identified a
            <strong>
              {" "}1-hour cross-sectional reversal factor
            </strong>
            . Assets with stronger relative
            previous-hour returns tended to rank
            weaker during the following hour, while
            recent relative losers tended to recover.
          </p>

          <p>
            The factor retained the expected negative
            Information Coefficient across Development,
            independent Validation, Final Time Holdout
            and Final Asset Holdout tests.
          </p>

          <div className="report-highlight">
            <ShieldCheck size={21} />

            <div>
              <strong>
                Final diagnosis
              </strong>

              <span>
                Validated historical signal evidence,
                but transaction-cost-sensitive
                implementation.
              </span>
            </div>
          </div>

        </ReportSection>


        {/* UNIVERSE */}

        <ReportSection
          number="02"
          title="Research Universe"
        >

          <div className="report-stat-grid">

            <ReportStat
              label="INITIAL REALITY PAIRS"
              value="2,587"
            />

            <ReportStat
              label="WEEKEND TRADABLE"
              value="90"
            />

            <ReportStat
              label="365-DAY UNIVERSE"
              value="24"
            />

            <ReportStat
              label="QUALITY APPROVED"
              value={
                tokens.totalTokens
              }
            />

          </div>


          <p>
            Data-quality filtering was based on
            historical availability and a corrected
            market-availability mask designed to
            distinguish genuine missing observations
            from systematic periods of market
            unavailability.
          </p>

        </ReportSection>


        {/* FACTOR DISCOVERY */}

        <ReportSection
          number="03"
          title="Factor Discovery"
        >

          <div className="report-stat-grid">

            <ReportStat
              label="CANDIDATES"
              value={
                factors.totalCandidates
              }
            />

            <ReportStat
              label="FINAL FACTOR"
              value="1H Reversal"
            />

            <ReportStat
              label="TARGET"
              value="Next 1H"
            />

            <ReportStat
              label="EXPECTED IC"
              value="Negative"
            />

          </div>


          <p>
            Candidate factors were investigated using
            the Development sample. The selected
            factor was frozen before independent
            validation results were inspected.
          </p>

        </ReportSection>


        {/* VALIDATION */}

        <ReportSection
          number="04"
          title="Independent Validation"
        >

          <table className="report-table">

            <thead>
              <tr>
                <th>
                  Stage
                </th>

                <th>
                  Mean IC
                </th>

                <th>
                  Median IC
                </th>

                <th>
                  Timestamps
                </th>
              </tr>
            </thead>


            <tbody>

              <ValidationRow
                name="Development"
                result={
                  results.development
                }
              />

              <ValidationRow
                name="Validation"
                result={
                  results.validation
                }
              />

              <ValidationRow
                name="Final Time Holdout"
                result={
                  results.timeHoldout
                }
              />

              <ValidationRow
                name="Final Asset Holdout"
                result={
                  results.assetHoldout
                }
              />

            </tbody>

          </table>


          <div className="report-pass-box">

            <CheckCircle2 size={19} />

            <span>
              The expected negative IC direction
              survived all four major research stages.
            </span>

          </div>

        </ReportSection>


        {/* EXECUTION */}

        <ReportSection
          number="05"
          title="Economic Implementation"
        >

          <table className="report-table">

            <thead>
              <tr>
                <th>
                  Test
                </th>

                <th>
                  0 bps
                </th>

                <th>
                  2.5 bps
                </th>

                <th>
                  Interpretation
                </th>
              </tr>
            </thead>


            <tbody>

              <ExecutionRow
                name="Validation"
                gross={
                  results.validationGross
                }
                cost={
                  results.validationCost
                }
              />

              <ExecutionRow
                name="Final Time"
                gross={
                  results.timeGross
                }
                cost={
                  results.timeCost
                }
              />

              <ExecutionRow
                name="Final Assets"
                gross={
                  results.assetGross
                }
                cost={
                  results.assetCost
                }
              />

            </tbody>

          </table>


          <div className="report-warning-box">

            <TriangleAlert
              size={19}
            />

            <span>
              Transaction-cost assumptions are
              hypothetical one-way sensitivities and
              are not claims about actual Bitget fees.
            </span>

          </div>

        </ReportSection>


        {/* METHODOLOGY */}

        <ReportSection
          number="06"
          title="Research Discipline"
        >

          <div className="report-methodology">

            <MethodStep
              number="1"
              text="Construct universe"
            />

            <MethodStep
              number="2"
              text="Apply data-quality rules"
            />

            <MethodStep
              number="3"
              text="Discover factors on Development only"
            />

            <MethodStep
              number="4"
              text="Freeze factor"
            />

            <MethodStep
              number="5"
              text="Independent validation"
            />

            <MethodStep
              number="6"
              text="Final time and asset holdouts"
            />

            <MethodStep
              number="7"
              text="Execution and cost study"
            />

            <MethodStep
              number="8"
              text="Factor autopsy"
            />

          </div>

        </ReportSection>


        {/* LIMITATIONS */}

        <ReportSection
          number="07"
          title="Limitations"
        >

          <p>
            The Final Asset Holdout contains only
            three assets, so rank-based IC values are
            naturally coarse. The broader Final Time
            Holdout provides more cross-sectional
            information.
          </p>

          <p>
            Portfolio Sharpe values reported in the
            research are naive annualized estimates
            and are not adjusted for serial
            dependence.
          </p>

          <p>
            Historical statistical validation does
            not guarantee future persistence or
            trading profitability.
          </p>

        </ReportSection>


        {/* CONCLUSION */}

        <ReportSection
          number="08"
          title="Final Conclusion"
        >

          <div className="report-final-verdict">

            <div>

              <span>
                STATISTICAL FACTOR
              </span>

              <strong className="report-success">
                VALIDATED
              </strong>

              <p>
                The historical reversal relationship
                survived independent validation and
                final holdout tests.
              </p>

            </div>


            <div>

              <span>
                ECONOMIC IMPLEMENTATION
              </span>

              <strong className="report-warning">
                COST-SENSITIVE
              </strong>

              <p>
                Frequent repositioning causes
                transaction-cost sensitivity and
                prevents the current implementation
                from being considered robust at all
                tested cost assumptions.
              </p>

            </div>

          </div>

        </ReportSection>


        <footer className="report-footer">

          rFactor Lab · Quant Research Engine
          <br />

          Historical research and hypothetical
          backtest analysis only.

        </footer>

      </article>

    </motion.div>
  );
}


/* =========================================================
   COMPONENTS
========================================================= */

function ReportSection({
  number,
  title,
  children,
}) {
  return (
    <section className="report-section">

      <div className="report-section-heading">
        <span>
          {number}
        </span>

        <h2>
          {title}
        </h2>
      </div>

      {children}

    </section>
  );
}


function ReportStat({
  label,
  value,
}) {
  return (
    <div className="report-stat">
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>
    </div>
  );
}


function ValidationRow({
  name,
  result,
}) {
  if (!result) {
    return null;
  }

  return (
    <tr>
      <td>
        {name}
      </td>

      <td>
        {result.meanIC.toFixed(4)}
      </td>

      <td>
        {result.medianIC.toFixed(4)}
      </td>

      <td>
        {result.timestamps.toLocaleString()}
      </td>
    </tr>
  );
}


function ExecutionRow({
  name,
  gross,
  cost,
}) {
  if (
    !gross ||
    !cost
  ) {
    return null;
  }

  return (
    <tr>
      <td>
        {name}
      </td>

      <td className="report-positive">
        {gross.returnPct >= 0
          ? "+"
          : ""}

        {gross.returnPct.toFixed(2)}%
      </td>

      <td
        className={
          cost.returnPct >= 0
            ? "report-positive"
            : "report-negative"
        }
      >
        {cost.returnPct >= 0
          ? "+"
          : ""}

        {cost.returnPct.toFixed(2)}%
      </td>

      <td>
        {cost.returnPct >= 0
          ? "Remains positive"
          : "Edge overwhelmed"}
      </td>
    </tr>
  );
}


function MethodStep({
  number,
  text,
}) {
  return (
    <div className="report-method-step">

      <span>
        {number}
      </span>

      <strong>
        {text}
      </strong>

    </div>
  );
}


export default ResearchReport;