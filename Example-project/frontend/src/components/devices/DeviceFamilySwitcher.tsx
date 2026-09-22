import type { DeviceFamily } from "../../services/api";

type Props = {
  family: DeviceFamily;
  onChange: (family: DeviceFamily) => void;
};

const options: { id: DeviceFamily; label: string }[] = [
  { id: "simulation", label: "Simulation" },
  { id: "edge", label: "Edge" },
];

export function DeviceFamilySwitcher({ family, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const selected = option.id === family;
        return (
          <button
            key={option.id}
            type="button"
            className={
              selected
                ? "rounded-md bg-emerald-700 px-3 py-1.5 text-sm font-medium text-white"
                : "rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            }
            onClick={() => onChange(option.id)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
