const express = require("express");
const cors = require("cors");
require("dotenv").config();

const fetch = (...args) =>
  import("node-fetch").then(({ default: fetch }) => fetch(...args));

// ✅ CREATE APP
const app = express();

// ✅ MIDDLEWARE
app.use(cors());
app.use(express.json());

// ✅ TEST ROUTE
app.get("/", (req, res) => {
  res.send("Planora backend is running 🚀");
});

// ✅ MAIN ROUTE
app.post("/plan-trip", async (req, res) => {
  try {
    const { destination } = req.body;

    const response = await fetch(
      `http://api.weatherstack.com/current?access_key=${process.env.WEATHER_API_KEY}&query=${destination}`,
    );

    const data = await response.json();

    console.log("WEATHER DATA:", data);

    // ❌ Handle API error
    if (data.error) {
      return res.json({ error: data.error.info });
    }

    res.json({
      weather: {
        temp: data.current.temperature,
        condition: data.current.weather_descriptions[0],
      },
      itinerary: [
        `Explore ${destination}`,
        "Visit top attractions",
        "Enjoy local food",
      ],
    });
  } catch (error) {
    console.error("SERVER ERROR:", error);
    res.json({ error: "Server crashed" });
  }
});

// ✅ START SERVER
app.listen(5000, () => {
  console.log("Server running on http://localhost:5000");
});
