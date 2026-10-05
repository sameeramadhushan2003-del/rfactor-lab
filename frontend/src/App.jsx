import ResearchCopilot from "./pages/ResearchCopilot";
import FactorAutopsy from "./pages/FactorAutopsy";
import Execution from "./pages/Execution";
import FactorValidation from "./pages/FactorValidation";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import FactorExplorer from "./pages/FactorExplorer";
import TokenExplorer from "./pages/TokenExplorer";
import ResearchTimeline from "./pages/ResearchTimeline";
import ResearchReport from "./pages/ResearchReport";

import {
  Activity,
  BarChart3,
  Bot,
  Clock3,
  FileText,
  BrainCircuit,
  FlaskConical,
  Gauge,
  Coins,
  Home,
  Layers3,
  ShieldCheck,
  TrendingDown,
  Zap,
} from "lucide-react";

import "./App.css";

const pages = [
  {
    id: "overview",
    name: "Overview",
    icon: Home,
  },
  {
  id: "tokens",
  name: "Token Explorer",
  icon: Coins,
},
  {
  id: "explorer",
  name: "Factor Explorer",
  icon: BarChart3,
},
  {
    id: "validation",
    name: "Factor Validation",
    icon: ShieldCheck,
  },
  {
  id: "execution",
  name: "Backtest & Execution",
  icon: Activity,
},
  {
    id: "autopsy",
    name: "Factor Autopsy",
    icon: FlaskConical,
  },
  {
  id: "timeline",
  name: "Research Timeline",
  icon: Clock3,
},
  {
  id: "copilot",
  name: "Research Copilot",
  icon: Bot,
},
{
  id: "report",
  name: "Research Report",
  icon: FileText,
},
];



const stats = [
  {
    label: "Final Factor",
    value: "1H Reversal",
    description: "Cross-sectional mean reversion",
    icon: Zap,
  },
  {
    label: "Development IC",
    value: "-0.0744",
    description: "240-day research period",
    icon: BarChart3,
  },
  {
    label: "Validation IC",
    value: "-0.0351",
    description: "Independent assets + future time",
    icon: ShieldCheck,
  },
  {
    label: "Final Holdout IC",
    value: "-0.0708",
    description: "Final unseen time period",
    icon: Gauge,
  },
];

const pipeline = [
  ["2,587", "Reality pairs"],
  ["90", "Weekend-tradable"],
  ["24", "365-day assets"],
  ["23", "Quality approved"],
  ["14", "Development assets"],
  ["6", "Validation assets"],
  ["3", "Final holdout assets"],
];

function Sidebar({ activePage, setActivePage }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <BrainCircuit size={27} />
        </div>

        <div>
          <h2>rFactor Lab</h2>
          <span>Quant Research Engine</span>
        </div>
      </div>

      <div className="nav-label">RESEARCH</div>

      <nav>
        {pages.map((page) => {
          const Icon = page.icon;

          return (
            <button
              key={page.id}
              className={
                activePage === page.id
                  ? "nav-item active"
                  : "nav-item"
              }
              onClick={() => setActivePage(page.id)}
            >
              <Icon size={19} />
              <span>{page.name}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="system-status">
          <span className="status-dot"></span>

          <div>
            <strong>Research Engine</strong>
            <small>All systems operational</small>
          </div>
        </div>
      </div>
    </aside>
  );
}

function StatCard({ item, index }) {
  const Icon = item.icon;

  return (
    <motion.div
      className="stat-card"
      initial={{
        opacity: 0,
        y: 25,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: index * 0.1,
        duration: 0.5,
      }}
      whileHover={{
        y: -6,
      }}
    >
      <div className="stat-card-top">
        <span>{item.label}</span>

        <div className="small-icon">
          <Icon size={18} />
        </div>
      </div>

      <h3>{item.value}</h3>

      <p>{item.description}</p>
    </motion.div>
  );
}

function Overview({ setActivePage }){
  return (
    <>
      <motion.section
        className="hero"
        initial={{
          opacity: 0,
          y: 20,
        }}
        animate={{
          opacity: 1,
          y: 0,
        }}
        transition={{
          duration: 0.7,
        }}
      >
        <div className="hero-glow glow-one"></div>
        <div className="hero-glow glow-two"></div>

        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-dot"></span>
            BITGET REALITY FACTOR RESEARCH
          </div>

          <h1>
            Discover.
            <br />
            <span>Validate.</span>
            <br />
            Autopsy.
          </h1>

          <p>
            A quantitative research platform for discovering
            and independently validating predictive factors
            across Bitget Reality rTokens.
          </p>

          <div className="hero-buttons">
            <button
  className="primary-button"
  onClick={() => setActivePage("validation")}
>
  <Zap size={18} />
  Explore Research
</button>

            <button
  className="secondary-button"
  onClick={() => {
    document
      .getElementById("methodology")
      ?.scrollIntoView({
        behavior: "smooth",
      });
  }}
>
  <Layers3 size={18} />
  View Methodology
</button>
          </div>
        </div>

        <div className="hero-visual">
          <motion.div
            className="signal-card"
            animate={{
              y: [0, -10, 0],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >
            <div className="signal-header">
              <div>
                <span>FINAL FACTOR</span>
                <h3>1H Reversal</h3>
              </div>

              <TrendingDown size={30} />
            </div>

            <div className="signal-score">
              <span>FINAL HOLDOUT IC</span>

              <strong>-0.0708</strong>
            </div>

            <div className="signal-line">
              <motion.div
                className="signal-line-fill"
                initial={{
                  width: 0,
                }}
                animate={{
                  width: "76%",
                }}
                transition={{
                  duration: 1.4,
                  delay: 0.5,
                }}
              ></motion.div>
            </div>

            <div className="signal-footer">
              <span className="validated">
                <ShieldCheck size={16} />
                VALIDATED
              </span>

              <span>1,066 timestamps</span>
            </div>
          </motion.div>
        </div>
      </motion.section>

      <section className="content-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">RESEARCH METRICS</span>
            <h2>Factor performance</h2>
          </div>

          <p>
            Evidence collected across development, validation
            and independent holdout periods.
          </p>
        </div>

        <div className="stats-grid">
          {stats.map((item, index) => (
            <StatCard
              key={item.label}
              item={item}
              index={index}
            />
          ))}
        </div>
      </section>

      <section className="content-section discovery-section">
        <div className="discovery-card">
          <div className="discovery-icon">
            <BrainCircuit size={28} />
          </div>

          <div>
            <span className="eyebrow">CORE DISCOVERY</span>

            <h2>
              Short-term cross-sectional reversal
            </h2>

            <p>
              rTokens that outperform during the previous
              hour tend to rank weaker in the following hour,
              while recent relative losers tend to recover.
            </p>

            <div className="discovery-flow">
              <div>
                <strong>Recent winner</strong>
                <span>High 1H momentum</span>
              </div>

              <span className="flow-arrow">→</span>

              <div className="negative-box">
                <strong>Expected reversal</strong>
                <span>Lower next-hour rank</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
  id="methodology"
  className="content-section"
>
        <div className="section-heading">
          <div>
            <span className="eyebrow">METHODOLOGY</span>
            <h2>Research pipeline</h2>
          </div>
        </div>

        <div className="pipeline">
          {pipeline.map(([number, text], index) => (
            <motion.div
              key={text}
              className="pipeline-item"
              initial={{
                opacity: 0,
                scale: 0.9,
              }}
              whileInView={{
                opacity: 1,
                scale: 1,
              }}
              viewport={{
                once: true,
              }}
              transition={{
                delay: index * 0.08,
              }}
            >
              <div className="pipeline-number">
                {number}
              </div>

              <span>{text}</span>

              {index !== pipeline.length - 1 && (
                <div className="connector"></div>
              )}
            </motion.div>
          ))}
        </div>
      </section>
    </>
  );
}

function PlaceholderPage({ title }) {
  return (
    <motion.div
      className="placeholder-page"
      initial={{
        opacity: 0,
        y: 20,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
    >
      <span className="eyebrow">RFACTOR LAB</span>
      <h1>{title}</h1>

      <p>
        We will build this section next using your real
        research data and interactive charts.
      </p>
    </motion.div>
  );
}

function App() {
  const [activePage, setActivePage] =
    useState("overview");

  return (
    <div className="app">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
      />

      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={activePage}
            initial={{
              opacity: 0,
              x: 15,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
            exit={{
              opacity: 0,
              x: -15,
            }}
            transition={{
              duration: 0.25,
            }}
          >
            {activePage === "overview" && (
  <Overview
    setActivePage={setActivePage}
  />
)}
{activePage === "tokens" && (
  <TokenExplorer />
)}
{activePage === "explorer" && (
  <FactorExplorer />
)}

            {activePage === "validation" && (
  <FactorValidation />
)}

            {activePage === "execution" && (
  <Execution />
)}

            {activePage === "autopsy" && (
  <FactorAutopsy />
)}
{activePage === "timeline" && (
  <ResearchTimeline />
)}
{activePage === "copilot" && (
  <ResearchCopilot />
)}
{activePage === "report" && (
  <ResearchReport />
)}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;