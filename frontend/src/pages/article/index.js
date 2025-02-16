import { useEffect, useState } from "react";
import MarkdownViewer from "../../components/MarkdownViewer/MarkdownViewer";
import Head from "next/head";
import { useRouter } from "next/router";
import { useNavBar } from "@/components/NavBar/NavBar";


export default function Article({}){

    const router = useRouter()
    const slug = router.query?.e

    const [entity, setEntity] = useState()
    const [entityFound, setEntityFound] = useState(undefined)
    const { setPath } = useNavBar()

    useEffect(() => {
        if (entity){
            setPath([
                {'href': {'pathname': `/articles`}, 'title': 'Articles'},
                {'href': {'pathname': `/article`, 'query': {'e': entity.slug}}, 'title': entity.title}
            ])
            return () => {
                setPath([])
            }
        }
        else {
            setPath([
                {'href': {'pathname': `/articles`}, 'title': 'Articles'}
            ])
            return () => {
                setPath([])
            }
        }
    }, [entity])

    useEffect(() => {
        async function getEntity(){
            try {
                const url = `${process.env.NEXT_PUBLIC_API}/api/page?slug=${slug}`
                const response = await fetch(url, {
                    'method': 'GET'
                })
                if (!response.ok){
                    throw Error("Response was not ok")
                }
                const myJson = await response.json()
                setEntity(myJson['entity'])
                setEntityFound(true)
            }
            catch(e) {
                console.log(e)
                setEntityFound(false)
            }
        }
        if (slug){
            getEntity()
        }
    }, [slug])

    return (
        <div>
            <Head>
                <title>{entity?.title}</title>
            </Head>
            {entityFound === false ? (
                <div>
                    {`Could not find page for '${slug}'`}
                </div>
            ) : (entity?.markdown ? (
                <MarkdownViewer>
                    {entity?.markdown}
                </MarkdownViewer>
            ) : (
                <div>
                    {`Page for ${entity?.title} is not yet written.`}
                </div>
            ))}
        </div>
    )
}
