import { useState, useEffect, useMemo } from "react"
import Link from "next/link"

export default function Home() {
    return (
        <div style={{'display': 'flex', 'flexDirection': 'column'}}>
            <div><Link href={'/articles'}>Articles</Link></div>
            <div><Link href={'/sources'}>Sources</Link></div>
        </div>
    );
}
