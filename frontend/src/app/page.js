"use client";

import { useEffect, useState } from "react";

export default function Home() {

    const [entities, setEntities] = useState([])
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
        <div>
            <div>
                Hello!
            </div>
            {entities.map((ent) => {
                return (
                    <div key={ent.slug}>
                        {ent.title}
                    </div>
                )
            })}
        </div>
    );
}
