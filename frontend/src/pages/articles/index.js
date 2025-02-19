import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import { useNavBar } from "@/components/NavBar/NavBar"

export default function Articles() {
    const [entities, setEntities] = useState([])
    const { setPath } = useNavBar()

    useEffect(() => {
        setPath([
            {'href': {'pathname': `/articles`}, 'title': 'Articles'}
        ])
        return () => {
            setPath([])
        }
    }, [])

    useEffect(() => {
        async function getEntities(){
            try {
                const url = `${process.env.NEXT_PUBLIC_API}/api/index`
                const response = await fetch(url, {
                    'method': 'GET'
                })
                if (!response.ok){
                    throw Error("Response was not ok")
                }
                const myJson = await response.json()
                setEntities(myJson['entities'])
            }
            catch(e) {
                console.log(e)
            }
        }
        getEntities()
    }, [])

    return (
        <div style={{'display': 'flex', 'flexDirection': 'column'}}>
            {entities.map((ent) => {
                return ent.is_written ? (
                    <div key={ent.slug}>
                        <Link href={{'pathname': `/article`, 'query': { 'e': ent.slug }}}>{ent.title}</Link>
                    </div>
                ) : (
                    <div key={ent.slug}>
                        <Link style={{'all': 'unset', 'cursor': 'default'}} href={{'pathname': `/article`, 'query': { 'e': ent.slug }}}>{ent.title}</Link>
                    </div>
                )
            })}
        </div>
    );
}
