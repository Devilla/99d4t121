export default function DayPicker({ days, selected, onSelect }) {
  return (
    <div className="day-picker">
      <label htmlFor="delivery-day">Delivery day</label>
      <select id="delivery-day" value={selected} onChange={(e) => onSelect(e.target.value)}>
        {days.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>
    </div>
  );
}
