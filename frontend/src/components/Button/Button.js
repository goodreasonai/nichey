

export default function Button({ value, onClick }) {
    return (
        <button onClick={onClick} style={{'padding': '5px'}}>{value}</button>
    )
}
