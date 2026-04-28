export default function Badge({ type }) {
  return <span className={`badge badge-${type.toLowerCase()}`}>{type}</span>;
}
