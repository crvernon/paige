import { useEffect } from "react";
import { useAppStore } from "../store/appStore";

const ORDER = ["COMPASS-GLM", "GCIMS", "ICoM", "IM3", "Puget Sound", "Other"];

export function PocSection() {
  const projects = useAppStore((s) => s.projects);
  const activeProject = useAppStore((s) => s.activeProject);
  const pointOfContact = useAppStore((s) => s.pointOfContact);
  const set = useAppStore((s) => s.set);

  const options = Array.from(
    new Set([activeProject, ...ORDER].filter((p) => projects[p]))
  );

  // Initialise POC to the active project's value.
  useEffect(() => {
    if (!pointOfContact && projects[activeProject]) {
      set("pointOfContact", projects[activeProject]);
    }
  }, [projects, activeProject, pointOfContact, set]);

  const parts = (pointOfContact || "").split("\n");

  return (
    <section className="card">
      <h3 className="section-title">Point of contact for the research</h3>
      <label className="mt-2 block text-sm text-gray-700">
        Select the project that funded the work:
      </label>
      <select
        className="input mt-1"
        value={
          Object.keys(projects).find(
            (k) => projects[k] === pointOfContact
          ) ?? activeProject
        }
        onChange={(e) => set("pointOfContact", projects[e.target.value] || "")}
      >
        {options.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>

      {pointOfContact && (
        <div className="mt-3 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          {parts.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      )}
    </section>
  );
}
