"use client";

import { useState } from "react";
import { backendApiBaseUrl } from "../lib/api";

type PriceArea = "DK1" | "DK2";

type DashboardCardProps = {
  title: string;
  description: string;
  area: PriceArea;
  futureEndpoint: string;
};

const priceAreas: PriceArea[] = ["DK1", "DK2"];

function DashboardCard({
  title,
  description,
  area,
  futureEndpoint
}: DashboardCardProps) {
  return (
    <section className="card" aria-labelledby={`${futureEndpoint}-title`}>
      <div className="card__header">
        <div>
          <h2 id={`${futureEndpoint}-title`}>{title}</h2>
          <p className="card__description">{description}</p>
        </div>
        <span className="status">Read-only</span>
      </div>
      <ul className="state-list" aria-label={`${title} integration states`}>
        <li>
          <strong>Placeholder</strong>
          <span>
            Awaiting backend API data for {area}. No frontend request is made in
            this shell.
          </span>
        </li>
        <li>
          <strong>Loading-ready</strong>
          <span>
            Reserved for a future loading state when a read-only backend
            endpoint is connected.
          </span>
        </li>
        <li>
          <strong>Error-ready</strong>
          <span>
            Reserved for future display of API errors without blocking page
            render.
          </span>
        </li>
      </ul>
    </section>
  );
}

export default function DashboardPage() {
  const [selectedArea, setSelectedArea] = useState<PriceArea>("DK1");

  return (
    <main className="dashboard">
      <div className="dashboard__inner">
        <header className="dashboard__header">
          <div>
            <p className="eyebrow">FlexSignal AI</p>
            <h1>FlexSignal AI</h1>
            <div className="scope-badge">
              Read-only decision support — no automatic control
            </div>
            <p className="lead">
              Minimal dashboard shell for Danish electricity decision support.
              This page keeps all behavior local to the browser and does not
              dispatch, activate, forecast, poll, or control energy assets.
            </p>
          </div>
          <div className="selector">
            <label htmlFor="price-area">Price area</label>
            <select
              id="price-area"
              value={selectedArea}
              onChange={(event) =>
                setSelectedArea(event.target.value as PriceArea)
              }
            >
              {priceAreas.map((area) => (
                <option key={area} value={area}>
                  {area}
                </option>
              ))}
            </select>
          </div>
        </header>

        <div className="summary">
          <DashboardCard
            title="Spot prices"
            description="Future read-only display area for backend spot price data."
            area={selectedArea}
            futureEndpoint="spot-prices"
          />
          <DashboardCard
            title="Power balance"
            description="Future read-only display area for backend power balance data."
            area={selectedArea}
            futureEndpoint="power-balance"
          />
        </div>

        <p className="api-note">
          Backend API base URL helper: <code>{backendApiBaseUrl}</code>
        </p>
      </div>
    </main>
  );
}
