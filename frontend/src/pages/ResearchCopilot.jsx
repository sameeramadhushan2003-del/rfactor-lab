import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import {
  Bot,
  BrainCircuit,
  Send,
  Sparkles,
  ShieldCheck,
  TriangleAlert,
  TrendingDown,
  RefreshCw,
  User,
} from "lucide-react";


const suggestions = [
  "What factor did rFactor Lab discover?",
  "Did the factor survive validation?",
  "Why is the strategy cost-sensitive?",
  "What happened in the final holdout?",
  "What is the live price of rNVDA?",
];


function ResearchCopilot() {

  const [research, setResearch] = useState(null);

  const [input, setInput] = useState("");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text:
        "I’m the rFactor Lab Research Copilot. Ask me about the discovered factor, validation, holdout testing, execution performance, or Factor Autopsy.",
    },
  ]);

  const [typing, setTyping] = useState(false);

  const bottomRef = useRef(null);


  useEffect(() => {

    fetch("/data/research.json")
      .then((response) => response.json())
      .then((data) => setResearch(data))
      .catch((error) =>
        console.error(
          "Could not load research data:",
          error
        )
      );

  }, []);


  useEffect(() => {

    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [messages, typing]);


  function findStage(stageName) {

    return research?.validation?.find(
      (item) =>
        item.stage === stageName
    );

  }


  function findExecution(
    test,
    cost
  ) {

    return research?.execution?.find(
      (item) =>
        item.test === test &&
        Number(item.costBps) ===
          Number(cost)
    );

  }


  function generateAnswer(question) {

    if (!research) {

      return "The research dataset is still loading.";

    }


    const q =
      question.toLowerCase();


    const development =
      findStage("Development");

    const validation =
      findStage("Validation");

    const timeHoldout =
      findStage("FinalTimeHoldout");

    const assetHoldout =
      findStage("FinalAssetHoldout");


    const finalGross =
      findExecution(
        "FinalTime20",
        0
      );

    const finalCost =
      findExecution(
        "FinalTime20",
        2.5
      );

    const assetGross =
      findExecution(
        "FinalAsset3",
        0
      );

    const assetCost =
      findExecution(
        "FinalAsset3",
        2.5
      );


    if (
      q.includes("what factor") ||
      q.includes("discover")
    ) {

      return (
        `rFactor Lab discovered a 1-hour cross-sectional reversal factor. ` +
        `Assets with stronger relative returns during the previous hour tended to rank weaker during the next hour, while recent relative losers tended to recover. ` +
        `The Development mean IC was ${development.meanIC.toFixed(4)}.`
      );

    }


    if (
      q.includes("validation") ||
      q.includes("survive")
    ) {

      return (
        `Yes. The factor kept the expected negative IC through every research stage. ` +
        `Development: ${development.meanIC.toFixed(4)}, ` +
        `Validation: ${validation.meanIC.toFixed(4)}, ` +
        `Final Time Holdout: ${timeHoldout.meanIC.toFixed(4)}, ` +
        `and Final Asset Holdout: ${assetHoldout.meanIC.toFixed(4)}. ` +
        `This means the reversal relationship survived both future-time and different-asset testing.`
      );

    }


    if (
      q.includes("cost") ||
      q.includes("friction") ||
      q.includes("transaction")
    ) {

      return (
        `The main problem is turnover. The portfolio frequently changes positions because the signal is recalculated every hour. ` +
        `On the 20-asset Final Time Holdout, gross return at 0 bps was ${finalGross.returnPct.toFixed(2)}%, ` +
        `but at the hypothetical 2.5 bps one-way cost it fell to ${finalCost.returnPct.toFixed(2)}%. ` +
        `So the predictive factor survives, but the current execution design is cost-sensitive.`
      );

    }


    if (
      q.includes("holdout") ||
      q.includes("final test")
    ) {

      return (
        `The factor performed strongly in the final holdout tests. ` +
        `Final Time Holdout mean IC was ${timeHoldout.meanIC.toFixed(4)} across ${timeHoldout.timestamps.toLocaleString()} timestamps. ` +
        `The separate AMD, GLW and META holdout produced a mean IC of ${assetHoldout.meanIC.toFixed(4)}. ` +
        `For portfolio execution, the 20-asset final period returned ${finalGross.returnPct.toFixed(2)}% gross, while the three-asset holdout returned ${assetGross.returnPct.toFixed(2)}% gross.`
      );

    }


    if (
      q.includes("limitation") ||
      q.includes("weakness") ||
      q.includes("problem")
    ) {

      return (
        `The biggest limitation is economic implementation rather than factor validity. ` +
        `The signal remained statistically stable, but even with turnover capped near 0.50 per hour, transaction costs materially reduced returns. ` +
        `For example, the three-asset final holdout changed from ${assetGross.returnPct.toFixed(2)}% gross to ${assetCost.returnPct.toFixed(2)}% at 2.5 bps.`
      );

    }


    if (
      q.includes("ic") ||
      q.includes("information coefficient")
    ) {

      return (
        `Information Coefficient measures how well the factor ranking matches the ranking of future returns. ` +
        `For this reversal factor, a negative IC is expected because strong previous-hour performers are expected to rank weaker in the next hour. ` +
        `The final time-holdout IC was ${timeHoldout.meanIC.toFixed(4)}.`
      );

    }


    if (
      q.includes("profitable") ||
      q.includes("profit")
    ) {

      return (
        `Gross portfolio results were positive in the final tests, but net profitability was not robust to transaction costs. ` +
        `At 0 bps, the Final Time Holdout returned ${finalGross.returnPct.toFixed(2)}%. ` +
        `At 2.5 bps one-way cost, it became ${finalCost.returnPct.toFixed(2)}%. ` +
        `So the current conclusion is: validated signal, cost-sensitive implementation.`
      );

    }


    return (
      `The current research conclusion is: the 1-hour cross-sectional reversal factor is statistically validated, ` +
      `but its hourly long-short implementation is sensitive to turnover and transaction costs. ` +
      `You can ask me about validation, holdouts, IC, transaction costs, or limitations.`
    );

  }


  async function sendMessage(text = input) {

  const cleaned = text.trim();

  if (!cleaned || typing) {
    return;
  }

  setMessages((previous) => [
    ...previous,
    {
      role: "user",
      text: cleaned,
    },
  ]);

  setInput("");
  setTyping(true);

  try {

    const response = await fetch(
      "http://127.0.0.1:8000/chat",
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          question: cleaned,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Backend error: ${response.status}`
      );
    }

    const result = await response.json();

    setMessages((previous) => [
      ...previous,
      {
        role: "assistant",
        text: result.answer,
      },
    ]);

  } catch (error) {

    console.error(
      "Copilot backend error:",
      error
    );

    setMessages((previous) => [
      ...previous,
      {
        role: "assistant",
        text:
          "I could not reach the research backend. Make sure the FastAPI server is running on port 8000.",
      },
    ]);

  } finally {

    setTyping(false);

  }
}


  function handleKeyDown(event) {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      sendMessage();

    }

  }


  return (

    <motion.div
      className="copilot-page"
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

      {/* HERO */}

      <section className="copilot-header">

        <div>

          <div className="hero-badge">

            <Sparkles size={12} />

            GROUNDED RESEARCH ASSISTANT

          </div>


          <h1>

            Ask the research.
            <br />

            <span>
              Not the hype.
            </span>

          </h1>


          <p>

            Explore the rFactor Lab results using a
            research assistant grounded in the actual
            validation, holdout and execution data.

          </p>

        </div>


        <motion.div
          className="copilot-context-card"
          initial={{
            opacity: 0,
            scale: 0.94,
          }}
          animate={{
            opacity: 1,
            scale: 1,
          }}
        >

          <BrainCircuit size={29} />


          <span>
            RESEARCH CONTEXT
          </span>


          <h2>
            rFactor Copilot
          </h2>


          <div className="context-items">

            <ContextRow
              icon={ShieldCheck}
              text="Validated signal"
              type="success"
            />

            <ContextRow
              icon={TrendingDown}
              text="1H reversal factor"
            />

            <ContextRow
              icon={RefreshCw}
              text="Turnover-aware execution"
            />

            <ContextRow
              icon={TriangleAlert}
              text="Cost-sensitive strategy"
              type="warning"
            />

          </div>

        </motion.div>

      </section>


      {/* CHAT */}

      <section className="content-section copilot-content">

        <div className="copilot-layout">


          {/* SUGGESTIONS */}

          <aside className="copilot-suggestions">

            <span className="eyebrow">
              SUGGESTED QUESTIONS
            </span>


            <h3>
              Explore the research
            </h3>


            <div className="suggestion-list">

              {suggestions.map(
                (question) => (

                  <button
                    key={question}
                    onClick={() =>
                      sendMessage(
                        question
                      )
                    }
                  >

                    <Sparkles
                      size={14}
                    />

                    {question}

                  </button>

                )
              )}

            </div>


            <div className="grounded-box">

              <ShieldCheck
                size={19}
              />

              <div>

                <strong>
                  Grounded answers
                </strong>

                <span>
                  Uses the exported project
                  research data.
                </span>

              </div>

            </div>

          </aside>


          {/* CHAT WINDOW */}

          <div className="copilot-chat">

            <div className="chat-header">

              <div className="chat-agent">

                <div className="agent-icon">

                  <Bot size={20} />

                </div>


                <div>

                  <strong>
                    rFactor Research Copilot
                  </strong>

                  <span>
                    Research context loaded
                  </span>

                </div>

              </div>


              <div className="online-status">

                <span></span>

                Online

              </div>

            </div>


            <div className="messages">

              <AnimatePresence>

                {messages.map(
                  (
                    message,
                    index
                  ) => (

                    <motion.div
                      key={index}
                      className={
                        message.role ===
                        "user"
                          ? "message user-message"
                          : "message assistant-message"
                      }
                      initial={{
                        opacity: 0,
                        y: 10,
                      }}
                      animate={{
                        opacity: 1,
                        y: 0,
                      }}
                    >

                      <div className="message-avatar">

                        {message.role ===
                        "user" ? (
                          <User
                            size={16}
                          />
                        ) : (
                          <Bot
                            size={16}
                          />
                        )}

                      </div>


                      <div className="message-bubble">

                        {message.text}

                      </div>

                    </motion.div>

                  )
                )}

              </AnimatePresence>


              {typing && (

                <motion.div
                  className="message assistant-message"
                  initial={{
                    opacity: 0,
                  }}
                  animate={{
                    opacity: 1,
                  }}
                >

                  <div className="message-avatar">

                    <Bot size={16} />

                  </div>


                  <div className="typing-bubble">

                    <span></span>
                    <span></span>
                    <span></span>

                  </div>

                </motion.div>

              )}


              <div ref={bottomRef}></div>

            </div>


            <div className="chat-input-area">

              <textarea
                value={input}
                onChange={(event) =>
                  setInput(
                    event.target.value
                  )
                }
                onKeyDown={
                  handleKeyDown
                }
                placeholder="Ask about the factor, validation, costs, holdouts..."
                rows={1}
              />


              <button
                onClick={() =>
                  sendMessage()
                }
                disabled={
                  !input.trim()
                }
              >

                <Send size={18} />

              </button>

            </div>


            <div className="chat-disclaimer">

              Research explanations only.
              Results are historical and
              hypothetical.

            </div>

          </div>

        </div>

      </section>

    </motion.div>

  );

}


function ContextRow({
  icon: Icon,
  text,
  type,
}) {

  return (

    <div
      className={`context-row ${
        type ?? ""
      }`}
    >

      <Icon size={15} />

      <span>
        {text}
      </span>

    </div>

  );

}


export default ResearchCopilot;