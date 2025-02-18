import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import { useNavBar } from "@/components/NavBar/NavBar"

export default function Sources() {
    const [sources, setSources] = useState([])
    const { setPath } = useNavBar()

    useEffect(() => {
        setPath([
            {'href': {'pathname': `/sources`}, 'title': 'Sources'}
        ])
        return () => {
            setPath([])
        }
    }, [])

    useEffect(() => {
        async function getSources(){
            try {
                const url = `${process.env.NEXT_PUBLIC_API}/api/sources`
                const response = await fetch(url, {
                    'method': 'GET'
                })
                if (!response.ok){
                    throw Error("Response was not ok")
                }
                const myJson = await response.json()
                setSources(myJson['sources'])
            }
            catch(e) {
                console.log(e)
            }
        }
        getSources()
    }, [])

    return (
        <div style={{'display': 'flex', 'flexDirection': 'column'}}>
            {sources.map((src) => {
                return (
                    <div key={src.id}>
                        <Link href={{'pathname': `/source`, 'query': { 'id': src.id }}}>{src.title}</Link>
                    </div>
                )
            })}
        </div>
    );
}
