
import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bath,
  BedDouble,
  Building2,
  CalendarDays,
  CheckCircle2,
  Compass,
  Gauge,
  House,
  LoaderCircle,
  Menu,
  Ruler,
  ShieldCheck,
  Sparkles,
  Trees,
  X,
} from "lucide-react";

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "https://haven-smart-house-price-prediction-1.onrender.com"
).replace(/\/+$/, "");

const initialForm = {
  OverallQual: "7",
  YearBuilt: "2005",
  YearRemodAdd: "2005",
  GrLivArea: "1800",
  TotalBsmtSF: "900",
  GarageCars: "2",
  FullBath: "2",
  TotRmsAbvGrd: "7",
};

const fields = [
  {
    name: "OverallQual",
    label: "Overall quality",
    help: "Overall material and finish quality, typically 1–10.",
    icon: Gauge,
    min: 1,
    max: 10,
    step: 1,
  },
  {
    name: "YearBuilt",
    label: "Year built",
    help: "The year the original structure was built.",
    icon: CalendarDays,
    min: 1800,
    max: 2035,
    step: 1,
  },
  {
    name: "YearRemodAdd",
    label: "Year remodeled",
    help: "Year of the most recent remodeling or addition.",
    icon: CalendarDays,
    min: 1800,
    max: 2035,
    step: 1,
  },
  {
    name: "GrLivArea",
    label: "Above-ground living area",
    help: "Living area above ground, in square feet.",
    icon: Ruler,
    min: 1,
    max: 20000,
    step: 1,
  },
  {
    name: "TotalBsmtSF",
    label: "Basement area",
    help: "Total basement area, in square feet.",
    icon: Building2,
    min: 0,
    max: 10000,
    step: 1,
  },
  {
    name: "GarageCars",
    label: "Garage capacity",
    help: "Number of cars the garage can hold.",
    icon: House,
    min: 0,
    max: 10,
    step: 1,
  },
  {
    name: "FullBath",
    label: "Full bathrooms",
    help: "Number of full bathrooms above ground.",
    icon: Bath,
    min: 0,
    max: 10,
    step: 1,
  },
  {
    name: "TotRmsAbvGrd",
    label: "Above-ground rooms",
    help: "Total rooms above ground, excluding bathrooms.",
    icon: BedDouble,
    min: 1,
    max: 30,
    step: 1,
  },
];

function formatNumber(value) {
  const number = Number(value);

  return Number.isFinite(number)
    ? new Intl.NumberFormat("en-US", {
        maximumFractionDigits: 0,
      }).format(number)
    : "—";
}

function dateLabel(value) {
  if (!value) return "Just now";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString();
}

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [activeView, setActiveView] = useState("predict");
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");

  const filledCount = useMemo(
    () =>
      fields.filter(
        (field) => String(form[field.name]).trim() !== ""
      ).length,
    [form]
  );

  useEffect(() => {
    let mounted = true;

    fetch(`${API_BASE}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend unavailable");
        }

        return response.json();
      })
      .then((data) => {
        if (mounted) {
          setApiStatus(
            data.model_loaded ? "online" : "model-error"
          );
        }
      })
      .catch(() => {
        if (mounted) setApiStatus("offline");
      });

    return () => {
      mounted = false;
    };
  }, []);

  function updateField(name, value) {
    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    setError("");
  }

  async function submitPrediction(event) {
    event.preventDefault();
    setError("");
    setPrediction(null);

    const payload = {};

    for (const field of fields) {
      const raw = form[field.name];

      if (raw === "" || !Number.isFinite(Number(raw))) {
        setError(
          `Please enter a valid value for ${field.label.toLowerCase()}.`
        );
        return;
      }

      const value = Number(raw);

      if (value < field.min || value > field.max) {
        setError(
          `${field.label} must be between ${field.min.toLocaleString()} and ${field.max.toLocaleString()}.`
        );
        return;
      }

      payload[field.name] = value;
    }

    if (payload.YearRemodAdd < payload.YearBuilt) {
      setError(
        "The remodeling year cannot be earlier than the original construction year."
      );
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Prediction failed. Please check your entries and try again."
        );
      }

      // The backend handles saving the prediction to SQLite.
      // The frontend only displays the current result.
      setPrediction(data);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the prediction service. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function navigate(view) {
    setActiveView(view);
    setMobileMenuOpen(false);

    if (view === "predict") {
      document
        .getElementById("predict")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      document
        .getElementById(view)
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  return (
    <div className="site-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#home"
          onClick={() => setActiveView("predict")}
          aria-label="Haven home"
        >
          <span className="brand-mark">
            <House size={20} strokeWidth={2.2} />
          </span>
          <span className="brand-name">
            Haven — Smart House Price Prediction.<span>.</span>
          </span>
        </a>

        <nav
          className={`nav-links ${mobileMenuOpen ? "nav-open" : ""}`}
          aria-label="Main navigation"
        >
          <button
            className={
              activeView === "predict"
                ? "nav-link active"
                : "nav-link"
            }
            onClick={() => navigate("predict")}
          >
            Predict price
          </button>

          <button
            className="nav-link"
            onClick={() => navigate("about")}
          >
            How it works
          </button>

          <button
            className="mobile-close"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </nav>

        <div className="topbar-actions">
          <span className={`service-status status-${apiStatus}`}>
            <span className="status-dot" />

            {apiStatus === "online"
              ? "Model online"
              : apiStatus === "checking"
                ? "Connecting"
                : apiStatus === "model-error"
                  ? "Model unavailable"
                  : "Service offline"}
          </span>

          <button
            className="nav-cta"
            onClick={() => navigate("predict")}
          >
            Get an estimate <ArrowRight size={16} />
          </button>

          <button
            className="mobile-menu"
            onClick={() =>
              setMobileMenuOpen((value) => !value)
            }
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <X size={21} />
            ) : (
              <Menu size={21} />
            )}
          </button>
        </div>
      </header>

      <main>
        <section className="hero" id="home">
          <div className="hero-copy">
            <div className="eyebrow">
              <Sparkles size={14} /> A smarter view of property value
            </div>

            <h1>
              Fine your home's<br />
              estimate <em>worth.</em>
            </h1>

            <p className="hero-description">
             Enter property details to get an estimated price from our trained model.
            </p>

            <div className="hero-actions">
              <button
                className="button button-primary"
                onClick={() => navigate("predict")}
              >
                Estimate a home <ArrowRight size={17} />
              </button>

              <button
                className="text-button"
                onClick={() => navigate("about")}
              >
                How it works <ArrowDownRight size={16} />
              </button>
            </div>

            <div className="hero-proof">
              <div className="proof-icon">
                <ShieldCheck size={18} />
              </div>

              <div>
                <strong>Model-powered estimate</strong>
                <span>
                  Built around a pre-trained regression model
                </span>
              </div>
            </div>
          </div>

          <div
            className="hero-visual"
            aria-label="Illustration of a modern home"
          >
            <div className="visual-topline">
              <span>PROPERTY INTELLIGENCE</span>
              <span className="visual-index">01 / 03</span>
            </div>

            <div className="house-scene">
              <div className="sun-orb" />
              <div className="scene-cloud cloud-one" />
              <div className="scene-cloud cloud-two" />
              <div className="hill hill-back" />
              <div className="hill hill-front" />
              <div className="house-shadow" />

              <div className="illustrated-house">
                <div className="roof-left" />
                <div className="roof-right" />

                <div className="house-body">
                  <div className="upper-window">
                    <span />
                    <span />
                    <span />
                    <span />
                  </div>

                  <div className="front-door">
                    <i />
                  </div>

                  <div className="lower-window">
                    <span />
                    <span />
                    <span />
                    <span />
                  </div>
                </div>

                <div className="garage">
                  <div className="garage-door">
                    <i />
                    <i />
                    <i />
                  </div>
                </div>

                <div className="porch-step" />
              </div>

              <div className="tree tree-left">
                <i />
                <b />
                <span />
              </div>

              <div className="tree tree-right">
                <i />
                <b />
                <span />
              </div>

              <div className="pathway" />
            </div>

            <div className="visual-caption">
              <div>
                <span className="caption-kicker">
                  A clearer picture
                </span>
                <strong>
                  Better-informed property decisions
                </strong>
              </div>

              <div className="caption-icon">
                <Compass size={20} />
              </div>
            </div>

            <div className="floating-note">
              <span className="floating-icon">
                <CheckCircle2 size={17} />
              </span>

              <span>
                <strong>Ready when you are</strong>
                <small>Eight property details</small>
              </span>
            </div>
          </div>

          <div className="hero-bottomline">
            <span>THOUGHTFUL DATA. CLEARER DECISIONS.</span>
            <span>
             Property values are estimates only and may differ from actual market prices. <ArrowDownRight size={13} />
            </span>
          </div>
        </section>

        <section className="workspace-section" id="workspace">
          <div className="section-heading">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" /> THE ESTIMATOR
              </div>
              <h2>Start with the details.</h2>
            </div>

            <p>
             Enter a few property details to get an estimated price from our trained machine-learning model.
            </p>
          </div>

          <div className="workspace-grid" id="predict">
            <section className="form-panel">
              <div className="panel-heading">
                <div className="panel-icon">
                  <House size={19} />
                </div>

                <div>
                  <h3>Property profile</h3>
                  <p>Enter the details below to begin.</p>
                </div>

                <span className="step-label">
                  01 <span>/ 01</span>
                </span>
              </div>

              <form onSubmit={submitPrediction}>
                <div className="form-grid">
                  {fields.map((field, index) => {
                    const Icon = field.icon;

                    return (
                      <label className="field" key={field.name}>
                        <span className="field-label">
                          <span className="field-icon">
                            <Icon size={15} />
                          </span>
                          {field.label}
                        </span>

                        <span className="input-wrap">
                          <input
                            type="number"
                            name={field.name}
                            value={form[field.name]}
                            min={field.min}
                            max={field.max}
                            step={field.step}
                            required
                            onChange={(event) =>
                              updateField(
                                field.name,
                                event.target.value
                              )
                            }
                            aria-describedby={`${field.name}-help`}
                          />

                          <span className="input-index">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                        </span>

                        <span
                          className="field-help"
                          id={`${field.name}-help`}
                        >
                          {field.help}
                        </span>
                      </label>
                    );
                  })}
                </div>

                {error && (
                  <div className="error-message" role="alert">
                    {error}
                  </div>
                )}

                <div className="form-bottom">
                  <div className="form-progress">
                    <span className="progress-count">
                      {filledCount.toString().padStart(2, "0")}
                    </span>

                    <span>of 08 details completed</span>

                    <div className="progress-track">
                      <span
                        style={{
                          width: `${(filledCount / 8) * 100}%`,
                        }}
                      />
                    </div>
                  </div>

                  <button
                    className="button button-primary submit-button"
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <LoaderCircle className="spin" size={17} />
                        Calculating…
                      </>
                    ) : (
                      <>
                        Predict house price <ArrowRight size={17} />
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="form-note">
                <ShieldCheck size={15} />
                <span>
                  Your estimate is generated by the model on the
                  backend. It is not a formal appraisal.
                </span>
              </div>
            </section>

            <aside className="result-panel">
              <div className="result-panel-top">
                <span className="result-label">
                  <span className="result-pulse" /> YOUR ESTIMATE
                </span>

                <span className="result-symbol">
                  <Sparkles size={17} />
                </span>
              </div>

              {prediction ? (
                <div className="result-ready">
                  <span className="result-overline">
                    MODEL PREDICTION
                  </span>

                  <div className="result-price">
                    {formatNumber(prediction.predicted_price)}
                  </div>

                  <p className="result-unit">
                    Price units depend on the dataset used to train
                    this model.
                  </p>

                  <div className="result-divider" />

                  <div className="result-meta">
                    <span>Prediction ID</span>
                    <strong>#{prediction.id}</strong>
                  </div>

                  <div className="result-meta">
                    <span>Created</span>
                    <strong>{dateLabel(prediction.created_at)}</strong>
                  </div>

                  <div className="result-success">
                    <CheckCircle2 size={17} />
                    Prediction saved successfully
                  </div>

                  <button
                    type="button"
                    className="result-reset"
                    onClick={() => {
                      setPrediction(null);
                      setForm(initialForm);
                      setError("");
                    }}
                  >
                    Estimate another property <ArrowRight size={15} />
                  </button>
                </div>
              ) : (
                <div className="result-empty">
                  <div className="result-illustration">
                    <div className="result-orbit orbit-one" />
                    <div className="result-orbit orbit-two" />

                    <div className="result-house-icon">
                      <House size={32} strokeWidth={1.4} />
                    </div>

                    <Sparkles
                      className="sparkle sparkle-a"
                      size={16}
                    />
                    <Sparkles
                      className="sparkle sparkle-b"
                      size={11}
                    />
                  </div>

                  <h3>
                    Your estimate
                    <br />
                    will appear here.
                  </h3>

                  <p>
                    Complete the property profile and run the model
                    to see its prediction.
                  </p>

                  <div className="result-checklist">
                    <span>
                      <CheckCircle2 size={15} /> Uses your trained model
                    </span>
                    <span>
                      <CheckCircle2 size={15} /> Saves successful results
                    </span>
                    <span>
                      <CheckCircle2 size={15} /> Keeps the result on this page
                    </span>
                  </div>
                </div>
              )}

              <div className="result-footer">
                <span>
                  <span className="footer-dot" />
                  {apiStatus === "online"
                    ? "Prediction service connected"
                    : "Checking prediction service"}
                </span>
                <span>HAVEN / ML</span>
              </div>
            </aside>
          </div>
        </section>

        <section className="how-section" id="about">
          <div className="how-intro">
            <div className="eyebrow">
              <span className="eyebrow-line" /> A SIMPLE PROCESS
            </div>

            <h2>
              Clarity, from
              <br />
              <em>the ground up.</em>
            </h2>

            <p>
              No complicated workflow. Just the key property details,
              a trained model, and an estimate you can use as a
              starting point.
            </p>
          </div>

          <div className="how-steps">
            <article className="how-step">
              <span className="how-number">01</span>
              <div className="how-icon">
                <House size={20} />
              </div>
              <h3>Describe the home</h3>
              <p>
                Enter quality, size, construction year, garage
                capacity, and other required details.
              </p>
              <span className="step-arrow">
                <ArrowUpRight size={17} />
              </span>
            </article>

            <article className="how-step">
              <span className="how-number">02</span>
              <div className="how-icon">
                <Gauge size={20} />
              </div>
              <h3>Run the model</h3>
              <p>
                FastAPI passes your validated inputs to your existing
                trained regression pipeline.
              </p>
              <span className="step-arrow">
                <ArrowUpRight size={17} />
              </span>
            </article>

            <article className="how-step">
              <span className="how-number">03</span>
              <div className="how-icon">
                <CheckCircle2 size={20} />
              </div>
              <h3>Review your estimate</h3>
              <p>
                See your prediction instantly. The backend can store
                the result for database records without displaying
                a history list here.
              </p>
              <span className="step-arrow">
                <ArrowUpRight size={17} />
              </span>
            </article>
          </div>
        </section>

        <section className="closing-banner">
          <div className="closing-mark">
            <House size={22} />
          </div>

          <div>
            <span>YOUR NEXT PROPERTY DECISION</span>
            <h2>Start with a clearer estimate.</h2>
          </div>

          <button
            className="button button-light"
            onClick={() => navigate("predict")}
          >
            Predict a price <ArrowRight size={17} />
          </button>
        </section>
      </main>

      <footer className="footer">
        <a
          className="brand footer-brand"
          href="#home"
          onClick={() => setActiveView("predict")}
        >
          <span className="brand-mark">
            <House size={18} />
          </span>

          <span className="brand-name">
            Haven — Smart House Price Prediction.<span>.</span>
          </span>
        </a>

        <span className="footer-copy">
          A model-powered starting point for property decisions.
        </span>

        <span className="footer-right">
          ESTIMATES ARE NOT APPRAISALS
          <span>© {new Date().getFullYear()} HAVEN</span>
        </span>
      </footer>
    </div>
  );
}
