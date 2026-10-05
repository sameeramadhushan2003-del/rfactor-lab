import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import {
  Activity,
  ArrowLeftRight,
  BarChart3,
  Coins,
  Database,
  Gauge,
  Search,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


/* =========================================================
   HELPERS
========================================================= */

function prettyGroup(group) {
  const names = {
    Development: "Development",
    Validation: "Validation",
    AssetHoldout: "Asset Holdout",
    Holdout: "Asset Holdout",
  };

  return names[group] ?? group;
}


/* =========================================================
   TOKEN EXPLORER
========================================================= */

function TokenExplorer() {
  /* -------------------------------------------------------
     STATE
  ------------------------------------------------------- */

  const [data, setData] = useState(null);

  const [selectedTicker, setSelectedTicker] =
    useState("NVDA");

  const [compareTicker, setCompareTicker] =
    useState("TSLA");

  const [range, setRange] =
    useState(30);

  const [search, setSearch] =
    useState("");

    const [liveMarket, setLiveMarket] =
  useState(null);

const [liveLoading, setLiveLoading] =
  useState(false);

const [liveError, setLiveError] =
  useState("");


  /* -------------------------------------------------------
     LOAD TOKEN DATA
  ------------------------------------------------------- */

  useEffect(() => {
    fetch("/data/tokens.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `Token data request failed: ${response.status}`
          );
        }

        return response.json();
      })

      .then((result) => {
        setData(result);

        if (!result.tokens?.length) {
          return;
        }

        const hasNVDA =
          result.tokens.some(
            (token) =>
              token.ticker === "NVDA"
          );

        if (!hasNVDA) {
          setSelectedTicker(
            result.tokens[0].ticker
          );
        }


        const hasTSLA =
          result.tokens.some(
            (token) =>
              token.ticker === "TSLA"
          );

        if (!hasTSLA) {
          const secondToken =
            result.tokens.find(
              (token) =>
                token.ticker !==
                result.tokens[0].ticker
            );

          if (secondToken) {
            setCompareTicker(
              secondToken.ticker
            );
          }
        }
      })

      .catch((error) => {
        console.error(
          "Could not load token data:",
          error
        );
      });
  }, []);


  /* -------------------------------------------------------
     SELECTED TOKEN
  ------------------------------------------------------- */

  const selected = useMemo(() => {
    if (!data) {
      return null;
    }

    return data.tokens.find(
      (token) =>
        token.ticker ===
        selectedTicker
    );
  }, [
    data,
    selectedTicker,
  ]);

  useEffect(() => {
  if (!selected?.rtokenSymbol) {
    return;
  }

  const controller =
    new AbortController();

  async function loadLiveMarket() {
    setLiveLoading(true);
    setLiveError("");

    try {
      const response =
        await fetch(
          `http://127.0.0.1:8000/bitget/ticker/${selected.rtokenSymbol}`,
          {
            signal:
              controller.signal,
          }
        );

      if (!response.ok) {
        throw new Error(
          `Request failed: ${response.status}`
        );
      }

      const result =
        await response.json();

      setLiveMarket(result);

    } catch (error) {
      if (
        error.name !==
        "AbortError"
      ) {
        console.error(
          "Could not load live Bitget data:",
          error
        );

        setLiveError(
          "Live Bitget market data unavailable."
        );

        setLiveMarket(null);
      }

    } finally {
      setLiveLoading(false);
    }
  }

  loadLiveMarket();

  return () => {
    controller.abort();
  };

}, [
  selected?.rtokenSymbol,
]);


  /* -------------------------------------------------------
     COMPARISON TOKEN
  ------------------------------------------------------- */

  const compareToken = useMemo(() => {
    if (!data) {
      return null;
    }

    return data.tokens.find(
      (token) =>
        token.ticker ===
        compareTicker
    );
  }, [
    data,
    compareTicker,
  ]);


  /* -------------------------------------------------------
     MAKE SURE TOKEN A AND TOKEN B ARE DIFFERENT
  ------------------------------------------------------- */

  useEffect(() => {
    if (
      !data ||
      selectedTicker !== compareTicker
    ) {
      return;
    }

    const alternative =
      data.tokens.find(
        (token) =>
          token.ticker !==
          selectedTicker
      );

    if (alternative) {
      setCompareTicker(
        alternative.ticker
      );
    }
  }, [
    data,
    selectedTicker,
    compareTicker,
  ]);


  /* -------------------------------------------------------
     FILTERED PRICE / RETURN CHART
  ------------------------------------------------------- */

  const filteredChart = useMemo(() => {
    if (!selected) {
      return [];
    }

    const chart =
      selected.chart ?? [];

    if (!chart.length) {
      return [];
    }

    const latestDate =
      new Date(
        chart[
          chart.length - 1
        ].datetime
      );

    const startDate =
      new Date(latestDate);

    startDate.setDate(
      startDate.getDate() -
      range
    );

    return chart.filter(
      (point) =>
        new Date(
          point.datetime
        ) >= startDate
    );
  }, [
    selected,
    range,
  ]);


  /* -------------------------------------------------------
     TOKEN COMPARISON CHART
  ------------------------------------------------------- */

  const comparisonChart = useMemo(() => {
    if (
      !selected ||
      !compareToken
    ) {
      return [];
    }

    const firstChart =
      selected.chart ?? [];

    const secondChart =
      compareToken.chart ?? [];

    if (
      !firstChart.length ||
      !secondChart.length
    ) {
      return [];
    }


    const latestFirst =
      new Date(
        firstChart[
          firstChart.length - 1
        ].datetime
      );

    const latestSecond =
      new Date(
        secondChart[
          secondChart.length - 1
        ].datetime
      );


    const latestDate =
      latestFirst < latestSecond
        ? latestFirst
        : latestSecond;


    const startDate =
      new Date(latestDate);

    startDate.setDate(
      startDate.getDate() -
      range
    );


    const firstMap =
      new Map(
        firstChart
          .filter(
            (point) =>
              new Date(
                point.datetime
              ) >= startDate
          )
          .map(
            (point) => [
              point.datetime,
              point.close,
            ]
          )
      );


    const secondMap =
      new Map(
        secondChart
          .filter(
            (point) =>
              new Date(
                point.datetime
              ) >= startDate
          )
          .map(
            (point) => [
              point.datetime,
              point.close,
            ]
          )
      );


    const commonDates =
      [...firstMap.keys()]
        .filter(
          (datetime) =>
            secondMap.has(datetime)
        )
        .sort();


    if (!commonDates.length) {
      return [];
    }


    const firstBase =
      firstMap.get(
        commonDates[0]
      );

    const secondBase =
      secondMap.get(
        commonDates[0]
      );


    if (
      !firstBase ||
      !secondBase
    ) {
      return [];
    }


    return commonDates.map(
      (datetime) => ({
        datetime,

        tokenA:
          (
            firstMap.get(datetime) /
            firstBase
          ) * 100,

        tokenB:
          (
            secondMap.get(datetime) /
            secondBase
          ) * 100,
      })
    );
  }, [
    selected,
    compareToken,
    range,
  ]);


  /* -------------------------------------------------------
     SNAPSHOT MOMENTUM RANK
  ------------------------------------------------------- */

  const tokenRank = useMemo(() => {
    if (
      !data ||
      !selected
    ) {
      return null;
    }

    const ranked =
      [...data.tokens]
        .filter(
          (token) =>
            Number.isFinite(
              token.latestMomentum1hPct
            )
        )
        .sort(
          (a, b) =>
            b.latestMomentum1hPct -
            a.latestMomentum1hPct
        );


    const index =
      ranked.findIndex(
        (token) =>
          token.ticker ===
          selected.ticker
      );


    if (index === -1) {
      return null;
    }


    return {
      rank: index + 1,
      total: ranked.length,
    };
  }, [
    data,
    selected,
  ]);


  /* -------------------------------------------------------
     UNIVERSE MEDIAN
  ------------------------------------------------------- */

  const universeMedian =
    useMemo(() => {
      if (!data) {
        return 0;
      }

      const values =
        data.tokens
          .map(
            (token) =>
              token.latestMomentum1hPct
          )
          .filter(
            (value) =>
              Number.isFinite(value)
          )
          .sort(
            (a, b) =>
              a - b
          );


      if (!values.length) {
        return 0;
      }


      const middle =
        Math.floor(
          values.length / 2
        );


      if (
        values.length % 2 === 0
      ) {
        return (
          values[middle - 1] +
          values[middle]
        ) / 2;
      }


      return values[middle];
    }, [data]);


  /* -------------------------------------------------------
     TOKEN SEARCH
  ------------------------------------------------------- */

  const searchedTokens =
    useMemo(() => {
      if (!data) {
        return [];
      }

      const query =
        search
          .trim()
          .toLowerCase();

      return data.tokens.filter(
        (token) =>
          `${token.ticker} ${token.displaySymbol} ${token.rtokenSymbol}`
            .toLowerCase()
            .includes(query)
      );
    }, [
      data,
      search,
    ]);


  /* -------------------------------------------------------
     LOADING
  ------------------------------------------------------- */

  if (
    !data ||
    !selected
  ) {
    return (
      <div className="validation-loading">
        Loading Token Explorer...
      </div>
    );
  }


  /* -------------------------------------------------------
     DERIVED VALUES
  ------------------------------------------------------- */

  const latestMomentum =
    Number(
      selected.latestMomentum1hPct
    );

  const momentumPositive =
    latestMomentum >= 0;

  const reversalInterpretation =
    latestMomentum >
    universeMedian
      ? "Recent relative strength"
      : "Recent relative weakness";


  /* ======================================================
     PAGE
  ====================================================== */

  return (
    <motion.div
      className="token-explorer-page"
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

      {/* ==================================================
          HERO
      ================================================== */}

      <section className="token-hero">
        <div>
          <div className="hero-badge">
            <Coins size={12} />

            RTOKEN UNIVERSE EXPLORER
          </div>


          <h1>
            Pick a token.
            <br />

            <span>
              Inspect the evidence.
            </span>
          </h1>


          <p>
            Explore the individual rTokens used in
            the factor research universe, including
            historical coverage, quality status,
            research split and recent price behavior.
          </p>
        </div>


        <motion.div
          className="token-universe-card"
          initial={{
            opacity: 0,
            scale: 0.95,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
        >
          <Database size={28} />

          <span>
            RESEARCH UNIVERSE
          </span>

          <strong>
            {data.totalTokens}
          </strong>

          <small>
            quality-approved rTokens exported
          </small>
        </motion.div>
      </section>


      <section className="content-section token-content">

        {/* ==================================================
            TOKEN SELECTOR
        ================================================== */}

        <div className="token-controls">
          <div className="token-select-group">
            <label>
              SELECT RTOKEN
            </label>

            <select
              value={selectedTicker}
              onChange={(event) =>
                setSelectedTicker(
                  event.target.value
                )
              }
            >
              {data.tokens.map(
                (token) => (
                  <option
                    key={token.ticker}
                    value={token.ticker}
                  >
                    {token.displaySymbol}
                    {" — "}
                    {token.rtokenSymbol}
                  </option>
                )
              )}
            </select>
          </div>


          <div className="token-selected-summary">
            <div className="token-symbol-box">
              {selected.displaySymbol}
            </div>

            <div>
              <span>
                SELECTED TOKEN
              </span>

              <strong>
                {selected.rtokenSymbol}
              </strong>
            </div>
          </div>


          <div
            className={
              selected.qualityOk
                ? "token-quality good"
                : "token-quality bad"
            }
          >
            <ShieldCheck size={18} />

            <div>
              <span>
                DATA QUALITY
              </span>

              <strong>
                {selected.qualityOk
                  ? "APPROVED"
                  : "REVIEW"}
              </strong>
            </div>
          </div>
        </div>

        {/* ==================================================
    LIVE BITGET MARKET
================================================== */}

<div className="bitget-live-card">

  <div className="bitget-live-header">

    <div>
      <span className="eyebrow">
        BITGET AGENT HUB
      </span>

      <h2>
        Live rToken Market
      </h2>
    </div>


    <div
      className={
        liveMarket?.connected
          ? "bitget-connection connected"
          : "bitget-connection"
      }
    >
      <span className="connection-dot" />

      {liveLoading
        ? "CONNECTING"
        : liveMarket?.connected
        ? "CONNECTED"
        : "OFFLINE"}
    </div>

  </div>


  {liveLoading && (
    <div className="bitget-loading">
      Loading live Bitget market data...
    </div>
  )}


  {liveError && (
    <div className="bitget-error">
      {liveError}
    </div>
  )}


  {liveMarket && (
    <>

      <div className="bitget-live-meta">

        <div>
          <span>
            SYMBOL
          </span>

          <strong>
            {liveMarket.symbol}
          </strong>
        </div>


        <div>
          <span>
            MODE
          </span>

          <strong className="readonly-text">
            {liveMarket.mode}
          </strong>
        </div>


        <div>
          <span>
            SOURCE
          </span>

          <strong>
            {liveMarket.integration}
          </strong>
        </div>

      </div>


      <div className="bitget-market-grid">

        <LiveMetric
          label="LIVE PRICE"
          value={
            Number(
              liveMarket.market.lastPrice
            ).toLocaleString(
              undefined,
              {
                maximumFractionDigits: 4,
              }
            )
          }
        />


        <LiveMetric
          label="24H CHANGE"
          value={
            `${
              Number(
                liveMarket.market.price24hPcnt
              ) >= 0
                ? "+"
                : ""
            }${(
              Number(
                liveMarket.market.price24hPcnt
              ) * 100
            ).toFixed(2)}%`
          }
          positive={
            Number(
              liveMarket.market.price24hPcnt
            ) >= 0
          }
        />


        <LiveMetric
          label="24H HIGH"
          value={
            Number(
              liveMarket.market.highPrice24h
            ).toLocaleString(
              undefined,
              {
                maximumFractionDigits: 4,
              }
            )
          }
        />


        <LiveMetric
          label="24H LOW"
          value={
            Number(
              liveMarket.market.lowPrice24h
            ).toLocaleString(
              undefined,
              {
                maximumFractionDigits: 4,
              }
            )
          }
        />


        <LiveMetric
          label="BEST BID"
          value={
            Number(
              liveMarket.market.bid1Price
            ).toLocaleString(
              undefined,
              {
                maximumFractionDigits: 4,
              }
            )
          }
        />


        <LiveMetric
          label="BEST ASK"
          value={
            Number(
              liveMarket.market.ask1Price
            ).toLocaleString(
              undefined,
              {
                maximumFractionDigits: 4,
              }
            )
          }
        />

      </div>


      <div className="bitget-live-footer">

        <span>
          Official Bitget Agent SDK
        </span>

        <span>
          Read-only market integration
        </span>

      </div>

    </>
  )}

</div>


        {/* ==================================================
            METRICS
        ================================================== */}

        <div className="token-metrics">
          <TokenMetric
            icon={Coins}
            label="HISTORICAL SNAPSHOT PRICE"
            value={
              Number(
                selected.latestPrice
              ).toLocaleString(
                undefined,
                {
                  maximumFractionDigits: 4,
                }
              )
            }
          />


          <TokenMetric
            icon={
              momentumPositive
                ? TrendingUp
                : TrendingDown
            }
            label="LATEST 1H RETURN"
            value={
              `${
                latestMomentum >= 0
                  ? "+"
                  : ""
              }${latestMomentum.toFixed(3)}%`
            }
          />


          <TokenMetric
            icon={Gauge}
            label="COVERAGE"
            value={
              `${Number(
                selected.coveragePct
              ).toFixed(2)}%`
            }
          />


          <TokenMetric
            icon={Database}
            label="HISTORY"
            value={
              `${Math.round(
                Number(
                  selected.historyDays
                )
              )} days`
            }
          />


          <TokenMetric
            icon={BarChart3}
            label="RESEARCH GROUP"
            value={
              prettyGroup(
                selected.group
              )
            }
          />


          <TokenMetric
            icon={Activity}
            label="SNAPSHOT RANK"
            value={
              tokenRank
                ? `${tokenRank.rank} / ${tokenRank.total}`
                : "N/A"
            }
          />
        </div>


        {/* ==================================================
            PRICE + TOKEN PROFILE
        ================================================== */}

        <div className="token-main-grid">

          {/* PRICE */}

          <div className="token-chart-card">
            <div className="token-chart-header">
              <div>
                <span className="eyebrow">
                  PRICE HISTORY
                </span>

                <h2>
                  {selected.displaySymbol}
                  {" "}
                  price
                </h2>
              </div>


              <div className="range-selector">
                {[7, 14, 30].map(
                  (days) => (
                    <button
                      key={days}
                      className={
                        range === days
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setRange(days)
                      }
                    >
                      {days}D
                    </button>
                  )
                )}
              </div>
            </div>


            <div className="token-chart">
              <ResponsiveContainer
                width="100%"
                height={330}
              >
                <AreaChart
                  data={filteredChart}
                >
                  <defs>
                    <linearGradient
                      id="priceGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor="#7865ff"
                        stopOpacity={0.28}
                      />

                      <stop
                        offset="95%"
                        stopColor="#7865ff"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>


                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="rgba(255,255,255,0.05)"
                  />


                  <XAxis
                    dataKey="datetime"
                    tickFormatter={
                      (value) =>
                        new Date(
                          value
                        ).toLocaleDateString(
                          undefined,
                          {
                            month: "short",
                            day: "numeric",
                          }
                        )
                    }
                    tick={{
                      fill: "#626d85",
                      fontSize: 9,
                    }}
                    axisLine={false}
                    tickLine={false}
                    minTickGap={40}
                  />


                  <YAxis
                    domain={[
                      "auto",
                      "auto",
                    ]}
                    tick={{
                      fill: "#626d85",
                      fontSize: 9,
                    }}
                    axisLine={false}
                    tickLine={false}
                    width={60}
                  />


                  <Tooltip
                    labelFormatter={
                      (value) =>
                        new Date(
                          value
                        ).toLocaleString()
                    }
                    contentStyle={{
                      background:
                        "#101727",
                      border:
                        "1px solid rgba(255,255,255,0.08)",
                      borderRadius:
                        "10px",
                    }}
                  />


                  <Area
                    type="monotone"
                    dataKey="close"
                    stroke="#806cff"
                    strokeWidth={2}
                    fill="url(#priceGradient)"
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>


          {/* TOKEN PROFILE */}

          <div className="token-profile-card">
            <span className="eyebrow">
              TOKEN PROFILE
            </span>


            <h2>
              {selected.displaySymbol}
            </h2>


            <ProfileRow
              label="Native ticker"
              value={
                selected.ticker
              }
            />


            <ProfileRow
              label="rToken symbol"
              value={
                selected.rtokenSymbol
              }
            />


            <ProfileRow
              label="Research split"
              value={
                prettyGroup(
                  selected.group
                )
              }
            />


            <ProfileRow
              label="Coverage"
              value={
                `${Number(
                  selected.coveragePct
                ).toFixed(2)}%`
              }
            />


            <ProfileRow
              label="Rows"
              value={
                Number(
                  selected.rows
                ).toLocaleString()
              }
            />


            <ProfileRow
              label="Factor eligible"
              value={
                selected.factorEligible
                  ? "Yes"
                  : "No"
              }
            />


            <ProfileRow
              label="Split frozen"
              value={
                selected.splitFrozen
                  ? "Yes"
                  : "No"
              }
            />


            <div className="token-interpretation">
              <span>
                REVERSAL CONTEXT
              </span>

              <strong>
                {reversalInterpretation}
              </strong>

              <p>
                This is a descriptive snapshot
                relative to the latest exported
                1-hour returns. The validated factor
                itself is cross-sectional and is
                evaluated across the full universe.
              </p>
            </div>
          </div>
        </div>


        {/* ==================================================
            1H RETURN CHART
        ================================================== */}

        <div className="token-momentum-card">
          <div className="token-chart-header">
            <div>
              <span className="eyebrow">
                FACTOR INPUT
              </span>

              <h2>
                1-hour return history
              </h2>
            </div>


            <div className="momentum-summary">
              Universe snapshot median:

              <strong>
                {" "}
                {universeMedian >= 0
                  ? "+"
                  : ""}

                {universeMedian.toFixed(3)}%
              </strong>
            </div>
          </div>


          <div className="token-chart">
            <ResponsiveContainer
              width="100%"
              height={290}
            >
              <LineChart
                data={filteredChart}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="rgba(255,255,255,0.05)"
                />


                <XAxis
                  dataKey="datetime"
                  tickFormatter={
                    (value) =>
                      new Date(
                        value
                      ).toLocaleDateString(
                        undefined,
                        {
                          month: "short",
                          day: "numeric",
                        }
                      )
                  }
                  tick={{
                    fill: "#626d85",
                    fontSize: 9,
                  }}
                  axisLine={false}
                  tickLine={false}
                  minTickGap={40}
                />


                <YAxis
                  tick={{
                    fill: "#626d85",
                    fontSize: 9,
                  }}
                  axisLine={false}
                  tickLine={false}
                  width={55}
                  tickFormatter={
                    (value) =>
                      `${value}%`
                  }
                />


                <Tooltip
                  labelFormatter={
                    (value) =>
                      new Date(
                        value
                      ).toLocaleString()
                  }
                  formatter={
                    (value) => [
                      `${Number(
                        value
                      ).toFixed(3)}%`,
                      "1H Return",
                    ]
                  }
                  contentStyle={{
                    background:
                      "#101727",
                    border:
                      "1px solid rgba(255,255,255,0.08)",
                    borderRadius:
                      "10px",
                  }}
                />


                <ReferenceLine
                  y={0}
                  stroke="rgba(255,255,255,0.18)"
                  strokeDasharray="4 4"
                />


                <Line
                  type="monotone"
                  dataKey="return1h"
                  stroke="#63c9ff"
                  strokeWidth={1.8}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>


        {/* ==================================================
            TOKEN COMPARISON
        ================================================== */}

        <div className="token-compare-section">

          <div className="token-library-header">
            <div>
              <span className="eyebrow">
                TOKEN COMPARE
              </span>

              <h2>
                Compare two rTokens
              </h2>
            </div>
          </div>


          {/* SELECTORS */}

          <div className="compare-controls">

            {/* TOKEN A */}

            <div className="compare-selector">
              <label>
                TOKEN A
              </label>

              <select
                value={
                  selectedTicker
                }
                onChange={
                  (event) =>
                    setSelectedTicker(
                      event.target.value
                    )
                }
              >
                {data.tokens.map(
                  (token) => (
                    <option
                      key={
                        token.ticker
                      }
                      value={
                        token.ticker
                      }
                    >
                      {
                        token.displaySymbol
                      }
                    </option>
                  )
                )}
              </select>
            </div>


            {/* VS */}

            <div className="compare-vs">
              <ArrowLeftRight
                size={21}
              />

              <span>
                VS
              </span>
            </div>


            {/* TOKEN B */}

            <div className="compare-selector">
              <label>
                TOKEN B
              </label>

              <select
                value={
                  compareTicker
                }
                onChange={
                  (event) =>
                    setCompareTicker(
                      event.target.value
                    )
                }
              >
                {data.tokens.map(
                  (token) => (
                    <option
                      key={
                        token.ticker
                      }
                      value={
                        token.ticker
                      }
                      disabled={
                        token.ticker ===
                        selectedTicker
                      }
                    >
                      {
                        token.displaySymbol
                      }
                    </option>
                  )
                )}
              </select>
            </div>
          </div>


          {/* COMPARISON CONTENT */}

          {compareToken && (
            <>
              <div className="compare-summary-grid">

                <CompareCard
                  token={selected}
                />


                <div className="compare-center">
                  <ArrowLeftRight
                    size={25}
                  />

                  <span>
                    COMPARISON
                  </span>
                </div>


                <CompareCard
                  token={
                    compareToken
                  }
                />

              </div>


              <div className="compare-chart-card">
                <div className="token-chart-header">

                  <div>
                    <span className="eyebrow">
                      RELATIVE PERFORMANCE
                    </span>

                    <h2>
                      {
                        selected.displaySymbol
                      }
                      {" vs "}
                      {
                        compareToken.displaySymbol
                      }
                    </h2>
                  </div>


                  <div className="comparison-legend">

                    <span className="legend-a">
                      {
                        selected.displaySymbol
                      }
                    </span>

                    <span className="legend-b">
                      {
                        compareToken.displaySymbol
                      }
                    </span>

                  </div>
                </div>


                <p className="compare-description">
                  Both price series are indexed to
                  100 at the beginning of the selected
                  period, allowing relative performance
                  to be compared directly.
                </p>


                {comparisonChart.length ? (
                  <div className="token-chart">

                    <ResponsiveContainer
                      width="100%"
                      height={330}
                    >
                      <LineChart
                        data={
                          comparisonChart
                        }
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          vertical={false}
                          stroke="rgba(255,255,255,0.05)"
                        />


                        <XAxis
                          dataKey="datetime"
                          tickFormatter={
                            (value) =>
                              new Date(
                                value
                              ).toLocaleDateString(
                                undefined,
                                {
                                  month:
                                    "short",
                                  day:
                                    "numeric",
                                }
                              )
                          }
                          tick={{
                            fill:
                              "#626d85",
                            fontSize:
                              9,
                          }}
                          axisLine={
                            false
                          }
                          tickLine={
                            false
                          }
                          minTickGap={
                            40
                          }
                        />


                        <YAxis
                          domain={[
                            "auto",
                            "auto",
                          ]}
                          tick={{
                            fill:
                              "#626d85",
                            fontSize:
                              9,
                          }}
                          axisLine={
                            false
                          }
                          tickLine={
                            false
                          }
                          width={55}
                        />


                        <Tooltip
                          labelFormatter={
                            (value) =>
                              new Date(
                                value
                              ).toLocaleString()
                          }
                          formatter={
                            (
                              value,
                              name
                            ) => [
                              Number(
                                value
                              ).toFixed(
                                2
                              ),
                              name,
                            ]
                          }
                          contentStyle={{
                            background:
                              "#101727",
                            border:
                              "1px solid rgba(255,255,255,0.08)",
                            borderRadius:
                              "10px",
                          }}
                        />


                        <ReferenceLine
                          y={100}
                          stroke="rgba(255,255,255,0.18)"
                          strokeDasharray="4 4"
                        />


                        <Line
                          type="monotone"
                          dataKey="tokenA"
                          name={
                            selected.displaySymbol
                          }
                          stroke="#806cff"
                          strokeWidth={2}
                          dot={false}
                        />


                        <Line
                          type="monotone"
                          dataKey="tokenB"
                          name={
                            compareToken.displaySymbol
                          }
                          stroke="#58c9f7"
                          strokeWidth={2}
                          dot={false}
                        />

                      </LineChart>
                    </ResponsiveContainer>

                  </div>
                ) : (
                  <div className="validation-loading">
                    No common chart timestamps
                    available for this comparison.
                  </div>
                )}

              </div>
            </>
          )}
        </div>


        {/* ==================================================
            TOKEN LIBRARY
        ================================================== */}

        <div className="token-library">

          <div className="token-library-header">

            <div>
              <span className="eyebrow">
                RTOKEN LIBRARY
              </span>

              <h2>
                Browse the universe
              </h2>
            </div>


            <div className="token-search">
              <Search size={15} />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
                placeholder="Search NVDA, AAPL, TSLA..."
              />
            </div>

          </div>


          <div className="token-grid">

            {searchedTokens.map(
              (token) => (

                <button
                  key={
                    token.ticker
                  }
                  className={
                    token.ticker ===
                    selectedTicker
                      ? "token-library-card selected"
                      : "token-library-card"
                  }
                  onClick={() => {
                    setSelectedTicker(
                      token.ticker
                    );

                    window.scrollTo({
                      top: 0,
                      behavior:
                        "smooth",
                    });
                  }}
                >

                  <div>
                    <strong>
                      {
                        token.displaySymbol
                      }
                    </strong>

                    <span>
                      {
                        token.rtokenSymbol
                      }
                    </span>
                  </div>


                  <div className="token-card-right">

                    <span
                      className={
                        token.latestMomentum1hPct >=
                        0
                          ? "positive"
                          : "negative"
                      }
                    >
                      {
                        token.latestMomentum1hPct >=
                        0
                          ? "+"
                          : ""
                      }

                      {Number(
                        token.latestMomentum1hPct
                      ).toFixed(2)}
                      %
                    </span>


                    <small>
                      {prettyGroup(
                        token.group
                      )}
                    </small>

                  </div>

                </button>

              )
            )}

          </div>

        </div>

      </section>

    </motion.div>
  );
}


/* =========================================================
   TOKEN METRIC
========================================================= */

function TokenMetric({
  icon: Icon,
  label,
  value,
}) {
  return (
    <motion.div
      className="token-metric"
      whileHover={{
        y: -4,
      }}
    >
      <div className="token-metric-icon">
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


/* =========================================================
   PROFILE ROW
========================================================= */

function ProfileRow({
  label,
  value,
}) {
  return (
    <div className="token-profile-row">
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>
    </div>
  );
}


/* =========================================================
   COMPARE CARD
========================================================= */

function CompareCard({
  token,
}) {
  const momentum =
    Number(
      token.latestMomentum1hPct
    );

  const positive =
    momentum >= 0;


  return (
    <motion.div
      className="compare-token-card"
      whileHover={{
        y: -4,
      }}
    >

      <div className="compare-token-heading">

        <div className="compare-token-symbol">
          {token.displaySymbol}
        </div>


        <div>
          <span>
            {token.rtokenSymbol}
          </span>

          <strong>
            {token.ticker}
          </strong>
        </div>

      </div>


      <div className="compare-stat">
        <span>
          Latest 1H return
        </span>

        <strong
          className={
            positive
              ? "compare-positive"
              : "compare-negative"
          }
        >
          {positive
            ? "+"
            : ""}

          {momentum.toFixed(3)}%
        </strong>
      </div>


      <div className="compare-stat">
        <span>
          Coverage
        </span>

        <strong>
          {Number(
            token.coveragePct
          ).toFixed(2)}
          %
        </strong>
      </div>


      <div className="compare-stat">
        <span>
          Research group
        </span>

        <strong>
          {prettyGroup(
            token.group
          )}
        </strong>
      </div>


      <div className="compare-stat">
        <span>
          Data quality
        </span>

        <strong
          className={
            token.qualityOk
              ? "compare-quality"
              : "compare-negative"
          }
        >
          {token.qualityOk
            ? "APPROVED"
            : "REVIEW"}
        </strong>
      </div>

    </motion.div>
  );
}

function LiveMetric({
  label,
  value,
  positive,
}) {
  return (
    <div className="bitget-live-metric">

      <span>
        {label}
      </span>

      <strong
        className={
          positive === true
            ? "live-positive"
            : positive === false
            ? "live-negative"
            : ""
        }
      >
        {value}
      </strong>

    </div>
  );
}
export default TokenExplorer;