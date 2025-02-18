import { useEffect, useState } from "react";
import MarkdownViewer from "../../components/MarkdownViewer/MarkdownViewer";
import Head from "next/head";
import { useRouter } from "next/router";
import { useNavBar } from "@/components/NavBar/NavBar";


export default function Source({}){

    const router = useRouter()
    const id = router.query?.id

    const [source, setSource] = useState()
    const [sourceFound, setSourceFound] = useState(undefined)
    const { setPath } = useNavBar()

    useEffect(() => {
        if (source){
            setPath([
                {'href': {'pathname': `/sources`}, 'title': 'Sources'},
                {'href': {'pathname': `/source`, 'query': {'id': source.id}}, 'title': source.title}
            ])
            return () => {
                setPath([])
            }
        }
        else {
            setPath([
                {'href': {'pathname': `/sources`}, 'title': 'Sources'}
            ])
            return () => {
                setPath([])
            }
        }
    }, [source])

    useEffect(() => {
        async function getSource(){
            try {
                const url = `${process.env.NEXT_PUBLIC_API}/api/source?id=${id}`
                const response = await fetch(url, {
                    'method': 'GET'
                })
                if (!response.ok){
                    throw Error("Response was not ok")
                }
                const myJson = await response.json()
                setSource(myJson['source'])
                setSourceFound(true)
            }
            catch(e) {
                console.log(e)
                setSourceFound(false)
            }
        }
        if (id){
            getSource()
        }
    }, [id])

    const info = [
        {'label': 'URL', 'value': (
            <a href={source?.url}>{source?.url}</a>
        ), 'hidden': !source?.url},
        {'label': 'Search Engine', 'value': source?.search_engine, 'hidden': !source?.search_engine},
        {'label': 'Query', 'value': source?.query, 'hidden': !source?.query},
        {'label': 'Snippet', 'value': source?.snippet, 'hidden': !source?.snippet}
    ]

    return (
        <div>
            <Head>
                <title>{source?.title}</title>
            </Head>
            {sourceFound === false ? (
                <div>
                    {`Could not find source with id '${id}'`}
                </div>
            ) : (source ? (
                <div style={{'display': 'flex', 'flexDirection': 'column', 'gap': '1rem'}}>
                    <h1>
                        {source.title}
                    </h1>
                    {info.filter((x) => !x.hidden).map((item) => {
                        return (
                            <div style={{'display': 'flex'}}>
                                <div style={{'flex': '1'}}>
                                    {item.label}
                                </div>
                                <div style={{'flex': '1'}}>
                                    {item.value}
                                </div>
                            </div>
                        )
                    })}
                </div>
            ) : "")}
        </div>
    )
}
