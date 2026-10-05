import {
  loadConfig,
  buildTools,
  BitgetRestClient,
  safeInvoke,
} from "@bitget-ai/bitget-agent-sdk";


/* =========================================================
   SYMBOL
========================================================= */

const inputSymbol =
  process.argv[2] || "RNVDAUSDT";

const symbol =
  inputSymbol
    .trim()
    .toUpperCase();


/* =========================================================
   BASIC SAFETY VALIDATION

   Only Reality/rToken-style USDT symbols are accepted.
========================================================= */

const validSymbol =
  /^R[A-Z0-9]+USDT$/.test(symbol);

if (!validSymbol) {

  console.error(
    JSON.stringify(
      {
        ok: false,
        error:
          "Invalid rToken symbol.",
        example:
          "RNVDAUSDT",
      },
      null,
      2
    )
  );

  process.exit(1);
}


/* =========================================================
   BITGET AGENT SDK CONFIGURATION

   MARKET MODULE ONLY
   READ-ONLY MODE
   NO TRADING
========================================================= */

const config =
  loadConfig({
    modules: "market",
    readOnly: true,
  });


/* =========================================================
   CLIENT
========================================================= */

const client =
  new BitgetRestClient(
    config
  );


const tools =
  buildTools(
    config
  );


const ctx = {
  config,
  client,
};


/* =========================================================
   FIND OFFICIAL MARKET TOOL
========================================================= */

const marketTool =
  tools.find(
    (tool) =>
      tool.name === "market"
  );


if (!marketTool) {

  console.error(
    JSON.stringify(
      {
        ok: false,
        error:
          "Bitget market tool was not loaded.",
      },
      null,
      2
    )
  );

  process.exit(1);
}


/* =========================================================
   FETCH PUBLIC RTOKEN TICKER
========================================================= */

try {

  const result =
    await safeInvoke(
      marketTool,
      {
        action:
          "tickers",

        category:
          "SPOT",

        symbol,
      },
      ctx
    );


  console.log(
    JSON.stringify(
      {
        integration:
          "Bitget Agent Hub",

        sdk:
          "@bitget-ai/bitget-agent-sdk",

        mode:
          "READ_ONLY",

        category:
          "SPOT",

        symbol,

        result,
      },
      null,
      2
    )
  );

} catch (error) {

  console.error(
    JSON.stringify(
      {
        ok: false,

        integration:
          "Bitget Agent Hub",

        mode:
          "READ_ONLY",

        symbol,

        error:
          error instanceof Error
            ? error.message
            : String(error),
      },
      null,
      2
    )
  );

  process.exit(1);
}